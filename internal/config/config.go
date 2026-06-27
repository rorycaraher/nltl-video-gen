package config

import (
	"fmt"
	"os"

	"github.com/rcaraher/nltl-video-gen/internal/preset"
	"gopkg.in/yaml.v3"
)

type Config struct {
	Presets []preset.Preset `yaml:"presets"`
}

func Load(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("reading %s: %w", path, err)
	}
	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("parsing %s: %w", path, err)
	}
	return &cfg, nil
}

func (c *Config) GetPreset(name string) (preset.Preset, bool) {
	for _, p := range c.Presets {
		if p.Name == name {
			return p, true
		}
	}
	return preset.Preset{}, false
}
