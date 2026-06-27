package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/rcaraher/nltl-video-gen/internal/config"
	"github.com/rcaraher/nltl-video-gen/internal/ffmpeg"
	"github.com/rcaraher/nltl-video-gen/internal/interactive"
	"github.com/rcaraher/nltl-video-gen/internal/preset"
	"github.com/rcaraher/nltl-video-gen/internal/profile"
	"github.com/spf13/cobra"
)

func main() {
	var (
		profileName string
		presetName  string
		bpm         int
		preview     bool
		outputDir   string
		configPath  string
	)

	root := &cobra.Command{
		Use:   "nltl-clip [audio] [image]",
		Short: "Generate social media video clips from audio and a still image",
		Args: func(cmd *cobra.Command, args []string) error {
			if len(args) == 0 || len(args) == 2 {
				return nil
			}
			return fmt.Errorf("expected 0 args (interactive) or 2 args (audio image), got %d", len(args))
		},
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) == 0 {
				choices, err := interactive.Run()
				if err != nil {
					return err
				}
				fmt.Println()
				if err := renderClip(choices.AudioPath, choices.ImagePath,
					choices.ProfileName, choices.PresetName,
					choices.BPM, false, "", ""); err != nil {
					return err
				}
				fmt.Printf("\nTo run this again without prompts:\n  %s\n", choices.HeadlessCommand())
				return nil
			}

			return renderClip(args[0], args[1], profileName, presetName, bpm, preview, outputDir, configPath)
		},
	}

	root.Flags().StringVarP(&profileName, "profile", "p", "instagram-square",
		"output profile (instagram-square, instagram-story, youtube)")
	root.Flags().StringVar(&presetName, "preset", "industrial",
		"visual preset (industrial, clean, dark, or custom from --config)")
	root.Flags().IntVar(&bpm, "bpm", 0, "track BPM for beat-synced animations (0 = time-based defaults)")
	root.Flags().BoolVar(&preview, "preview", false, "render a 10s low-quality preview")
	root.Flags().StringVarP(&outputDir, "output-dir", "o", "", "output directory (default: same as audio file)")
	root.Flags().StringVarP(&configPath, "config", "c", "", "YAML config file with custom presets")

	root.AddCommand(presetsCmd(), profilesCmd())

	if err := root.Execute(); err != nil {
		os.Exit(1)
	}
}

func renderClip(audioPath, imagePath, profileName, presetName string, bpm int, preview bool, outputDir, configPath string) error {
	prof, ok := profile.Get(profileName)
	if !ok {
		return fmt.Errorf("unknown profile %q — try: %s", profileName, strings.Join(profile.Names(), ", "))
	}

	var p preset.Preset
	if configPath != "" {
		cfg, err := config.Load(configPath)
		if err != nil {
			return fmt.Errorf("loading config: %w", err)
		}
		if cp, found := cfg.GetPreset(presetName); found {
			p = cp
		} else if bp, found := preset.Get(presetName); found {
			p = bp
		} else {
			return fmt.Errorf("preset %q not found in config or built-ins — built-ins: %s",
				presetName, strings.Join(preset.Names(), ", "))
		}
	} else {
		var found bool
		p, found = preset.Get(presetName)
		if !found {
			return fmt.Errorf("unknown preset %q — try: %s", presetName, strings.Join(preset.Names(), ", "))
		}
	}

	duration, err := ffmpeg.GetDuration(audioPath)
	if err != nil {
		return fmt.Errorf("reading audio duration: %w", err)
	}

	base := strings.TrimSuffix(filepath.Base(audioPath), filepath.Ext(audioPath))
	outDir := outputDir
	if outDir == "" {
		outDir = filepath.Dir(audioPath)
	}

	suffix := prof.Suffix
	if preview {
		suffix += "_preview"
	}
	outputPath := filepath.Join(outDir, fmt.Sprintf("%s_%s.mp4", base, suffix))

	filter := p.BuildFilter(prof.Width, prof.Height, bpm)

	fmt.Printf("Profile:  %s (%dx%d)\n", prof.Name, prof.Width, prof.Height)
	fmt.Printf("Preset:   %s — %s\n", p.Name, p.Description)
	if bpm > 0 {
		fmt.Printf("BPM:      %d\n", bpm)
	}
	if preview {
		fmt.Printf("Preview:  10s low-quality render\n")
	}
	fmt.Printf("Output:   %s\n\n", outputPath)

	return ffmpeg.Render(ffmpeg.Options{
		ImagePath:  imagePath,
		AudioPath:  audioPath,
		OutputPath: outputPath,
		Filter:     filter,
		Duration:   duration,
		Preview:    preview,
	})
}

func presetsCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "presets",
		Short: "List available built-in presets",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Built-in presets:")
			for _, name := range preset.Names() {
				p, _ := preset.Get(name)
				fmt.Printf("  %-14s %s\n", name, p.Description)
			}
		},
	}
}

func profilesCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "profiles",
		Short: "List available output profiles",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Output profiles:")
			for _, name := range profile.Names() {
				p, _ := profile.Get(name)
				fmt.Printf("  %-22s %dx%d\n", name, p.Width, p.Height)
			}
		},
	}
}
