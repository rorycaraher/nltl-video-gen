package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/rcaraher/nltl-video-gen/internal/config"
	"github.com/rcaraher/nltl-video-gen/internal/ffmpeg"
	"github.com/rcaraher/nltl-video-gen/internal/interactive"
	"github.com/rcaraher/nltl-video-gen/internal/preset"
	"github.com/rcaraher/nltl-video-gen/internal/profile"
	"github.com/spf13/cobra"
)

var (
	labelStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("241"))
	valueStyle  = lipgloss.NewStyle().Bold(true)
	accentStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("212")).Bold(true)
)

func label(s string) string { return labelStyle.Render(fmt.Sprintf("%-10s", s)) }

func main() {
	var (
		profileName string
		presetName  string
		bpm         int
		preview     bool
		still       bool
		verbose     bool
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
					choices.BPM, false, choices.Still, false, "", ""); err != nil {
					return err
				}
				fmt.Printf("\nTo run this again without prompts:\n  %s\n", choices.HeadlessCommand())
				return nil
			}

			return renderClip(args[0], args[1], profileName, presetName, bpm, preview, still, verbose, outputDir, configPath)
		},
	}

	root.Flags().StringVarP(&profileName, "profile", "p", "instagram-square",
		"output profile (instagram-square, instagram-story, youtube)")
	root.Flags().StringVar(&presetName, "preset", "industrial",
		"visual preset (industrial, clean, dark, or custom from --config)")
	root.Flags().IntVar(&bpm, "bpm", 0, "track BPM for beat-synced animations (0 = time-based defaults)")
	root.Flags().BoolVar(&preview, "preview", false, "render a 10s low-quality preview")
	root.Flags().BoolVar(&still, "still", false, "disable spatial motion (zoom, jitter) — keeps brightness pulsing")
	root.Flags().BoolVarP(&verbose, "verbose", "v", false, "show raw ffmpeg output during render")
	root.Flags().StringVarP(&outputDir, "output-dir", "o", "", "output directory (default: same as audio file)")
	root.Flags().StringVarP(&configPath, "config", "c", "", "YAML config file with custom presets")

	root.AddCommand(presetsCmd(), profilesCmd())

	if err := root.Execute(); err != nil {
		os.Exit(1)
	}
}

func renderClip(audioPath, imagePath, profileName, presetName string, bpm int, preview, still, verbose bool, outputDir, configPath string) error {
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

	if still {
		p.ZoomAmp = 0
		p.JitterAmp = 0
		p.ZoomBase = 1.0
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

	fmt.Println()
	fmt.Println(label("Profile") + valueStyle.Render(fmt.Sprintf("%s (%dx%d)", prof.Name, prof.Width, prof.Height)))
	fmt.Println(label("Preset") + valueStyle.Render(fmt.Sprintf("%s — %s", p.Name, p.Description)))
	if bpm > 0 {
		fmt.Println(label("BPM") + valueStyle.Render(fmt.Sprintf("%d", bpm)))
	}
	if preview {
		fmt.Println(label("Preview") + valueStyle.Render("10s low-quality render"))
	}
	if still {
		fmt.Println(label("Still") + valueStyle.Render("yes (spatial motion disabled)"))
	}
	fmt.Println(label("Output") + accentStyle.Render(outputPath))
	fmt.Println()

	return ffmpeg.Render(ffmpeg.Options{
		ImagePath:  imagePath,
		AudioPath:  audioPath,
		OutputPath: outputPath,
		Filter:     filter,
		Duration:   duration,
		Preview:    preview,
		Verbose:    verbose,
	})
}

func presetsCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "presets",
		Short: "List available built-in presets",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println(valueStyle.Render("Built-in presets:"))
			for _, name := range preset.Names() {
				p, _ := preset.Get(name)
				fmt.Printf("  %s  %s\n",
					valueStyle.Render(fmt.Sprintf("%-14s", name)),
					labelStyle.Render(p.Description),
				)
			}
		},
	}
}

func profilesCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "profiles",
		Short: "List available output profiles",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println(valueStyle.Render("Output profiles:"))
			for _, name := range profile.Names() {
				p, _ := profile.Get(name)
				fmt.Printf("  %s  %s\n",
					valueStyle.Render(fmt.Sprintf("%-22s", name)),
					labelStyle.Render(fmt.Sprintf("%dx%d", p.Width, p.Height)),
				)
			}
		},
	}
}
