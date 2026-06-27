package ffmpeg

import (
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"strings"
)

type Options struct {
	ImagePath  string
	AudioPath  string
	OutputPath string
	Filter     string
	Duration   float64
	Preview    bool
}

func GetDuration(audioPath string) (float64, error) {
	cmd := exec.Command("ffprobe",
		"-v", "error",
		"-show_entries", "format=duration",
		"-of", "default=noprint_wrappers=1:nokey=1",
		audioPath,
	)
	out, err := cmd.Output()
	if err != nil {
		return 0, fmt.Errorf("ffprobe: %w", err)
	}
	return strconv.ParseFloat(strings.TrimSpace(string(out)), 64)
}

func Render(opts Options) error {
	duration := opts.Duration
	if opts.Preview && duration > 10 {
		duration = 10
	}

	args := []string{
		"-y",
		"-loop", "1",
		"-i", opts.ImagePath,
		"-i", opts.AudioPath,
		"-vf", opts.Filter,
		"-c:v", "libx264",
	}

	if opts.Preview {
		args = append(args, "-preset", "ultrafast", "-crf", "35")
	} else {
		args = append(args, "-tune", "stillimage", "-crf", "18")
	}

	args = append(args,
		"-pix_fmt", "yuv420p",
		"-c:a", "aac",
		"-b:a", "192k",
		"-r", "30",
		"-t", fmt.Sprintf("%.3f", duration),
		"-shortest",
		opts.OutputPath,
	)

	cmd := exec.Command("ffmpeg", args...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}
