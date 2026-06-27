package preset

import (
	"fmt"
	"sort"
)

type Preset struct {
	Name               string  `yaml:"name"`
	Description        string  `yaml:"description"`
	ZoomBase           float64 `yaml:"zoom_base"`
	ZoomAmp            float64 `yaml:"zoom_amp"`
	ZoomBeats          float64 `yaml:"zoom_beats"`
	JitterAmp          float64 `yaml:"jitter_amp"`
	BlurSigma          float64 `yaml:"blur_sigma"`
	Contrast           float64 `yaml:"contrast"`
	Saturation         float64 `yaml:"saturation"`
	BrightnessAmp      float64 `yaml:"brightness_amp"`
	BrightnessBeats    float64 `yaml:"brightness_beats"`
	VignetteFraction   float64 `yaml:"vignette_fraction"` // multiplied by PI
	GrainStrength      int     `yaml:"grain_strength"`
}

var BuiltIn = map[string]Preset{
	"industrial": {
		Name:             "industrial",
		Description:      "Desaturated, grainy, heavy vignette — the default techno aesthetic",
		ZoomBase:         1.02,
		ZoomAmp:          0.01,
		ZoomBeats:        8.0,
		JitterAmp:        2.0,
		BlurSigma:        0.6,
		Contrast:         1.15,
		Saturation:       0.7,
		BrightnessAmp:    0.02,
		BrightnessBeats:  4.0,
		VignetteFraction: 0.167,
		GrainStrength:    25,
	},
	"clean": {
		Name:             "clean",
		Description:      "Full colour, minimal grain, subtle movement",
		ZoomBase:         1.01,
		ZoomAmp:          0.005,
		ZoomBeats:        16.0,
		JitterAmp:        1.0,
		BlurSigma:        0.3,
		Contrast:         1.05,
		Saturation:       1.0,
		BrightnessAmp:    0.01,
		BrightnessBeats:  8.0,
		VignetteFraction: 0.10,
		GrainStrength:    8,
	},
	"dark": {
		Name:             "dark",
		Description:      "Deep blacks, extreme grain, maximum vignette",
		ZoomBase:         1.03,
		ZoomAmp:          0.015,
		ZoomBeats:        4.0,
		JitterAmp:        3.0,
		BlurSigma:        0.8,
		Contrast:         1.30,
		Saturation:       0.4,
		BrightnessAmp:    0.04,
		BrightnessBeats:  2.0,
		VignetteFraction: 0.25,
		GrainStrength:    40,
	},
}

func Get(name string) (Preset, bool) {
	p, ok := BuiltIn[name]
	return p, ok
}

func Names() []string {
	names := make([]string, 0, len(BuiltIn))
	for k := range BuiltIn {
		names = append(names, k)
	}
	sort.Strings(names)
	return names
}

func (p Preset) BuildFilter(width, height, bpm int) string {
	var zoomExpr, jitterXExpr, jitterYExpr, brightnessExpr string

	if bpm > 0 {
		// BPM-synced: period in frames at 30fps
		zoomFramePeriod := p.ZoomBeats * 60.0 / float64(bpm) * 30.0
		zoomExpr = fmt.Sprintf("%.4f+%.4f*sin(2*PI*on/%.2f)", p.ZoomBase, p.ZoomAmp, zoomFramePeriod)

		jitterFramePeriod := 2.0 * 60.0 / float64(bpm) * 30.0
		jitterXExpr = fmt.Sprintf("iw/2-(iw/zoom/2)+%.1f*sin(2*PI*on/%.2f)", p.JitterAmp, jitterFramePeriod)
		jitterYExpr = fmt.Sprintf("ih/2-(ih/zoom/2)+%.1f*cos(2*PI*on/%.2f)", p.JitterAmp, jitterFramePeriod*0.9)

		brightnessFreq := float64(bpm) / (p.BrightnessBeats * 60.0)
		brightnessExpr = fmt.Sprintf("%.4f*sin(2*PI*t*%.4f)", p.BrightnessAmp, brightnessFreq)
	} else {
		// Time-based defaults matching the original script feel
		zoomExpr = fmt.Sprintf("%.4f+%.4f*sin(2*PI*on/200)", p.ZoomBase, p.ZoomAmp)
		jitterXExpr = fmt.Sprintf("iw/2-(iw/zoom/2)+%.1f*sin(on/7)", p.JitterAmp)
		jitterYExpr = fmt.Sprintf("ih/2-(ih/zoom/2)+%.1f*cos(on/9)", p.JitterAmp)
		brightnessExpr = fmt.Sprintf("%.4f*sin(2*PI*t*0.6)", p.BrightnessAmp)
	}

	return fmt.Sprintf(
		"scale=%d:%d:force_original_aspect_ratio=increase,"+
			"crop=%d:%d,"+
			"zoompan=z='%s':x='%s':y='%s':d=1:fps=30:s=%dx%d,"+
			"gblur=sigma=%.1f:steps=1,"+
			"eq=brightness='%s':contrast=%.2f:saturation=%.2f,"+
			"vignette=PI*%.3f,"+
			"noise=alls=%d:allf=t+u",
		width, height,
		width, height,
		zoomExpr, jitterXExpr, jitterYExpr, width, height,
		p.BlurSigma,
		brightnessExpr, p.Contrast, p.Saturation,
		p.VignetteFraction,
		p.GrainStrength,
	)
}
