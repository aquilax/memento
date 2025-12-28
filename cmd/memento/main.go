package main

import (
	"context"
	"log"
	"os"

	"github.com/aquilax/memento/internal/export"
	"github.com/aquilax/memento/internal/serve"
	"github.com/aquilax/memento/internal/tools"
	"github.com/urfave/cli/v3"
)

func main() {
	cmd := &cli.Command{
		Name: "memento",
		Commands: []*cli.Command{
			{
				Name:   "serve",
				Usage:  "serve",
				Action: serve.CmdServe,
				Flags: []cli.Flag{
					&cli.IntFlag{
						Name:  "port",
						Value: 8800,
					},
					&cli.StringFlag{
						Name:  "contacts",
						Value: "data/contacts.json",
					},
					&cli.StringFlag{
						Name:  "messages",
						Value: "data/messages.jsonl",
					},
				},
			},
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
	if err := cmd.Run(context.Background(), os.Args); err != nil {
		log.Fatal(err)
	}
}
