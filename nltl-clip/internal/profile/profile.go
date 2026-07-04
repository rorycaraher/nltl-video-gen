package profile

import "sort"

type Profile struct {
	Name   string
	Width  int
	Height int
	Suffix string
}

var Profiles = map[string]Profile{
	"instagram-square": {
		Name:   "instagram-square",
		Width:  1080,
		Height: 1080,
		Suffix: "instagram_square",
	},
	"instagram-story": {
		Name:   "instagram-story",
		Width:  1080,
		Height: 1920,
		Suffix: "instagram_story",
	},
	"youtube": {
		Name:   "youtube",
		Width:  1920,
		Height: 1080,
		Suffix: "youtube",
	},
}

func Get(name string) (Profile, bool) {
	p, ok := Profiles[name]
	return p, ok
}

func Names() []string {
	names := make([]string, 0, len(Profiles))
	for k := range Profiles {
		names = append(names, k)
	}
	sort.Strings(names)
	return names
}
