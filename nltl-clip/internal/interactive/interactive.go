package interactive

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/charmbracelet/huh"
	"github.com/rcaraher/nltl-video-gen/internal/preset"
	"github.com/rcaraher/nltl-video-gen/internal/profile"
)

var audioExts = map[string]bool{
	".wav": true, ".mp3": true, ".aiff": true, ".aif": true, ".flac": true,
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
	Still       bool
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
	if c.Still {
		parts = append(parts, "--still")
	}
	parts = append(parts, c.AudioPath, c.ImagePath)
	return strings.Join(parts, " ")
}

func Run() (*Choices, error) {
	audioFiles, err := scanFiles(audioExts)
	if err != nil {
		return nil, err
	}
	if len(audioFiles) == 0 {
		return nil, fmt.Errorf("no audio files found in current directory")
	}

	imageFiles, err := scanFiles(imageExts)
	if err != nil {
		return nil, err
	}
	if len(imageFiles) == 0 {
		return nil, fmt.Errorf("no image files found in current directory")
	}

	var (
		audioPath   = audioFiles[0]
		imagePath   = imageFiles[0]
		profileName = profile.Names()[0]
		presetName  = preset.Names()[0]
		bpmStr      = ""
		still       = false
	)

	form := huh.NewForm(
		huh.NewGroup(
			huh.NewSelect[string]().
				Title("Audio file").
				Options(fileOptions(audioFiles)...).
				Value(&audioPath),
			huh.NewSelect[string]().
				Title("Image file").
				Options(fileOptions(imageFiles)...).
				Value(&imagePath),
		),
		huh.NewGroup(
			huh.NewSelect[string]().
				Title("Profile").
				Options(profileOptions()...).
				Value(&profileName),
			huh.NewSelect[string]().
				Title("Preset").
				Options(presetOptions()...).
				Value(&presetName),
		),
		huh.NewGroup(
			huh.NewInput().
				Title("BPM").
				Description("Tempo-synced animations — leave blank to disable").
				Placeholder("e.g. 140").
				Validate(validateBPM).
				Value(&bpmStr),
			huh.NewConfirm().
				Title("Disable motion effects?").
				Description("Suggested for photograph inputs").
				Value(&still),
		),
	)

	if err := form.Run(); err != nil {
		if errors.Is(err, huh.ErrUserAborted) {
			return nil, fmt.Errorf("cancelled")
		}
		return nil, err
	}

	bpm := 0
	if bpmStr != "" {
		bpm, _ = strconv.Atoi(bpmStr)
	}

	return &Choices{
		AudioPath:   audioPath,
		ImagePath:   imagePath,
		ProfileName: profileName,
		PresetName:  presetName,
		BPM:         bpm,
		Still:       still,
	}, nil
}

func scanFiles(exts map[string]bool) ([]string, error) {
	entries, err := os.ReadDir(".")
	if err != nil {
		return nil, err
	}
	var files []string
	for _, e := range entries {
		if !e.IsDir() && exts[strings.ToLower(filepath.Ext(e.Name()))] {
			files = append(files, e.Name())
		}
	}
	return files, nil
}

func fileOptions(files []string) []huh.Option[string] {
	opts := make([]huh.Option[string], len(files))
	for i, f := range files {
		opts[i] = huh.NewOption(f, f)
	}
	return opts
}

func profileOptions() []huh.Option[string] {
	names := profile.Names()
	opts := make([]huh.Option[string], len(names))
	for i, name := range names {
		p, _ := profile.Get(name)
		label := fmt.Sprintf("%-22s %dx%d", name, p.Width, p.Height)
		opts[i] = huh.NewOption(label, name)
	}
	return opts
}

func presetOptions() []huh.Option[string] {
	names := preset.Names()
	opts := make([]huh.Option[string], len(names))
	for i, name := range names {
		p, _ := preset.Get(name)
		label := fmt.Sprintf("%-14s %s", name, p.Description)
		opts[i] = huh.NewOption(label, name)
	}
	return opts
}

func validateBPM(s string) error {
	if s == "" {
		return nil
	}
	n, err := strconv.Atoi(s)
	if err != nil || n <= 0 {
		return fmt.Errorf("enter a positive number or leave blank")
	}
	return nil
}
