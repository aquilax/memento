package export

import (
	"context"
	"fmt"

	"github.com/urfave/cli/v3"
)

func CmdTelegramReader(ctx context.Context, cmd *cli.Command) error {
	fmt.Println("new task template: ", cmd.Args().First())
	return nil
}
