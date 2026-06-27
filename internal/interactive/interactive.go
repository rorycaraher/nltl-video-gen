package interactive

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/rcaraher/nltl-video-gen/internal/preset"
	"github.com/rcaraher/nltl-video-gen/internal/profile"
)

var audioExts = map[string]bool{
	".wav": true, ".mp3": true, ".aiff": true, ".flac": true,
}

var imageExts = map[string]bool{
	".jpg": true, ".jpeg": true, ".png": true,
}

type Choices struct {
	AudioPath   string
	ImagePath   string
	ProfileName string
	PresetName  string
	BPM         int
}

func (c *Choices) HeadlessCommand() string {
	parts := []string{
		"nltl-clip",
		"--profile", c.ProfileName,
		"--preset", c.PresetName,
	}
	if c.BPM > 0 {
		parts = append(parts, "--bpm", strconv.Itoa(c.BPM))
	}
	parts = append(parts, c.AudioPath, c.ImagePath)
	return strings.Join(parts, " ")
}

func Run() (*Choices, error) {
	reader := bufio.NewReader(os.Stdin)
	fmt.Println("No arguments provided — running interactively.\n")

	audioPath, err := pickFile(reader, "Audio file", audioExts)
	if err != nil {
		return nil, err
	}

	imagePath, err := pickFile(reader, "Image file", imageExts)
	if err != nil {
		return nil, err
	}

	profileName, err := pickProfile(reader)
	if err != nil {
		return nil, err
	}

	presetName, err := pickPreset(reader)
	if err != nil {
		return nil, err
	}

	bpm, err := pickBPM(reader)
	if err != nil {
		return nil, err
	}

	return &Choices{
		AudioPath:   audioPath,
		ImagePath:   imagePath,
		ProfileName: profileName,
		PresetName:  presetName,
		BPM:         bpm,
	}, nil
}

func pickFile(reader *bufio.Reader, label string, exts map[string]bool) (string, error) {
	entries, err := os.ReadDir(".")
	if err != nil {
		return "", err
	}

	var files []string
	for _, e := range entries {
		if !e.IsDir() && exts[strings.ToLower(filepath.Ext(e.Name()))] {
			files = append(files, e.Name())
		}
	}

	if len(files) == 0 {
		return "", fmt.Errorf("no matching files found in current directory for %s", label)
	}

	fmt.Printf("%s:\n", label)
	for i, f := range files {
		fmt.Printf("  %d. %s\n", i+1, f)
	}

	chosen, err := pickNumbered(reader, len(files))
	if err != nil {
		return "", err
	}
	return files[chosen], nil
}

func pickProfile(reader *bufio.Reader) (string, error) {
	names := profile.Names()
	fmt.Println("\nProfile:")
	for i, name := range names {
		p, _ := profile.Get(name)
		fmt.Printf("  %d. %-22s %dx%d\n", i+1, name, p.Width, p.Height)
	}
	chosen, err := pickNumbered(reader, len(names))
	if err != nil {
		return "", err
	}
	return names[chosen], nil
}

func pickPreset(reader *bufio.Reader) (string, error) {
	names := preset.Names()
	fmt.Println("\nPreset:")
	for i, name := range names {
		p, _ := preset.Get(name)
		fmt.Printf("  %d. %-14s %s\n", i+1, name, p.Description)
	}
	chosen, err := pickNumbered(reader, len(names))
	if err != nil {
		return "", err
	}
	return names[chosen], nil
}

func pickBPM(reader *bufio.Reader) (int, error) {
	fmt.Print("\nBPM (press Enter to skip): ")
	line, err := reader.ReadString('\n')
	if err != nil {
		return 0, err
	}
	line = strings.TrimSpace(line)
	if line == "" {
		return 0, nil
	}
	n, err := strconv.Atoi(line)
	if err != nil || n <= 0 {
		fmt.Println("  Invalid BPM — skipping beat-sync.")
		return 0, nil
	}
	return n, nil
}

func pickNumbered(reader *bufio.Reader, count int) (int, error) {
	for {
		fmt.Print("  → ")
		line, err := reader.ReadString('\n')
		if err != nil {
			return 0, err
		}
		n, err := strconv.Atoi(strings.TrimSpace(line))
		if err != nil || n < 1 || n > count {
			fmt.Printf("  Enter a number between 1 and %d\n", count)
			continue
		}
		return n - 1, nil
	}
}
