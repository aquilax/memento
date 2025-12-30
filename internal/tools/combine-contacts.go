package tools

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"

	"github.com/aquilax/memento/pkg/ty"
	"github.com/samber/lo"
	"github.com/urfave/cli/v3"
)

func CmdCombineContacts(ctx context.Context, cmd *cli.Command) error {
	acc := map[string]ty.Contact{}
	files := cmd.StringSlice("file")
	for _, fileName := range files {
		f, err := os.Open(fileName)
		if err != nil {
			return errors.Join(fmt.Errorf("error opening file: %s", fileName), err)
		}
		var c []ty.Contact
		dec := json.NewDecoder(f)
		if err = dec.Decode(&c); err != nil {
			return errors.Join(fmt.Errorf("error parsing file: %s", fileName), err)
		}
		if err := mergeContacts(acc, c); err != nil {
			return err
		}
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(lo.Values(acc))
}

func mergeContacts(target map[string]ty.Contact, addition []ty.Contact) error {
	for i := range addition {
		name := addition[i].Name
		if _, found := target[name]; !found {
			target[name] = addition[i]
		} else {
			target[name] = ty.Contact{
				Name:      name,
				Platforms: append(target[name].Platforms, addition[i].Platforms...),
			}
		}
	}
	return nil
}