package ffmpeg

import (
	"fmt"
	"io"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"time"
)

type Options struct {
	ImagePath  string
	AudioPath  string
	OutputPath string
	Filter     string
	Duration   float64
	Preview    bool
	Verbose    bool
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

	if opts.Verbose {
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		return cmd.Run()
	}

	cmd.Stdout = io.Discard
	cmd.Stderr = io.Discard
	return runWithSpinner("Rendering", cmd.Run)
}

func runWithSpinner(title string, fn func() error) error {
	frames := []string{"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"}
	done := make(chan error, 1)
	go func() { done <- fn() }()

	i := 0
	line := fmt.Sprintf("  %s", title)
	for {
		select {
		case err := <-done:
			fmt.Printf("\r%s\r", strings.Repeat(" ", len(line)+4))
			return err
		default:
			fmt.Printf("\r%s %s", frames[i%len(frames)], line)
			i++
			time.Sleep(80 * time.Millisecond)
		}
	}
}
