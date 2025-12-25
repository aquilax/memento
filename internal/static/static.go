package static

import (
	"embed"
	"io/fs"
)

//go:embed assets
var content embed.FS

func GetEmbedFS() fs.FS {
	f, err := fs.Sub(content, "assets")
	if err != nil {
		panic(err)
	}
	return f
}
