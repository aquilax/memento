package main

import (
	"context"
	"os"

	"github.com/aquilax/memento/internal/export"
	"github.com/aquilax/memento/internal/tools"
	"github.com/urfave/cli/v3"
)

func main() {
	cmd := &cli.Command{
		Name: "memento",
		Commands: []*cli.Command{
			{
				Name:  "tools",
				Usage: "data tools",
				Commands: []*cli.Command{
					{
						Name:   "combine-contacts",
						Usage:  "Combine multiple contacts files",
						Action: tools.CmdCombineContacts,
						Flags: []cli.Flag{
							&cli.StringSliceFlag{
								Name:    "file",
								Aliases: []string{"f"},
							},
						},
					},
				},
			},
			{
				Name:  "export",
				Usage: "export database in specific format",
				Commands: []*cli.Command{
					{
						Name:   "telegram-reader",
						Usage:  "export messages in a format compatible with Telegram-Chat-Export-Reader",
						Action: export.CmdTelegramReader,
					},
				},
			},
		},
	}
	cmd.Run(context.Background(), os.Args)
}
