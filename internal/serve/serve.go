package serve

import (
	"bufio"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/aquilax/memento/internal/static"
	"github.com/aquilax/memento/pkg/ty"
	"github.com/samber/lo"
	"github.com/urfave/cli/v3"
)

const maxPage = 30

type filterFunc func(m *ty.Message) bool

type Server struct {
	Port             string
	ContactsFileName string
	MessagesFileName string
	log              *slog.Logger
}

func CmdServe(ctx context.Context, cmd *cli.Command) error {
	port := cmd.Int("port")
	contactsFileName := cmd.String("contacts")
	messagesFileName := cmd.String("messages")
	log := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{}))

	server := &Server{
		Port:             strconv.Itoa(port),
		ContactsFileName: contactsFileName,
		MessagesFileName: messagesFileName,
		log:              log,
	}

	return server.Start()
}

func (s *Server) Start() error {
	mux := http.NewServeMux()
	mux.Handle("/api/contacts", s.contactsHandler())
	mux.Handle("/api/messages", s.messagesHandler())
	mux.Handle("/", http.FileServerFS(static.GetEmbedFS()))
	address := "127.0.0.1:" + s.Port
	s.log.Info("http server listening", slog.Any("url", "http://"+address))
	return http.ListenAndServe(address, mux)
}

func (s *Server) contactsHandler() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		log := s.log.WithGroup("contactsHandler")
		start := time.Now()
		defer func() {
			log.Info(r.RequestURI, slog.Any("duration", time.Now().Sub(start)))
		}()

		f, err := os.Open(s.ContactsFileName)
		if err != nil {
			log.Error(err.Error())
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}
		defer f.Close()

		if _, err := io.Copy(w, f); err != nil {
			log.Error(err.Error())
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}
	})
}

func (s *Server) messagesHandler() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		log := s.log.WithGroup("messagesHandler")
		start := time.Now()
		defer func() {
			log.Info(r.RequestURI, slog.Any("duration", time.Now().Sub(start)))
		}()

		filters := []filterFunc{}

		if r.URL.Query().Has("contact_id") {
			userID := r.URL.Query().Get("contact_id")
			filters = append(filters, func(m *ty.Message) bool {
				return m.From == ty.UserID(userID) ||
					(m.To.MessageTargetType == ty.MessageTargetTypeUser && m.To.UserID != nil && *m.To.UserID == ty.UserID(userID))
			})
		}

		cursor := r.URL.Query().Get("cursor")
		if cursor != "" {
			if tm, err := time.Parse(time.RFC3339, cursor); err == nil {
				filters = append(filters, func(m *ty.Message) bool {
					return m.Timestamp.After(tm)
				})
			}
		}

		limit := maxPage
		var err error
		if r.URL.Query().Has("limit") {
			limit, err = strconv.Atoi(r.URL.Query().Get("limit"))
			if err != nil {
				log.Error(err.Error())
				http.Error(w, "Bad Request", http.StatusBadRequest)
				return
			}
			if limit > maxPage || limit < 1 {
				limit = maxPage
			}
		}

		result, err := walkMessages(s.MessagesFileName, limit, filters)
		if err != nil {
			log.Error(err.Error())
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}

		var nextCursor *string
		nextPage := func() *string {
			if len(result) < limit {
				return nil // less than we requested, no cursor
			}
			if last, found := lo.Last(result); found {
				nextUrl := *r.URL
				query := nextUrl.Query()
				nextCursor = lo.ToPtr(last.Timestamp.Format(time.RFC3339))
				query.Set("cursor", *nextCursor)
				nextUrl.RawQuery = query.Encode()

				return lo.ToPtr(nextUrl.String())
			}

			return nil
		}()

		enc := json.NewEncoder(w)
		enc.Encode(struct {
			Messages   []ty.Message `json:"messages"`
			NextPage   *string      `json:"next_page"`
			NextCursor *string      `json:"next_cursor"`
			Count      int          `json:"count"`
		}{
			Messages:   result,
			NextPage:   nextPage,
			NextCursor: nextCursor,
			Count:      len(result),
		})
	})
}

func walkMessages(fileName string, limit int, filters []filterFunc) ([]ty.Message, error) {
	line := -1
	count := 0
	result := []ty.Message{}
	f, err := os.Open(fileName)
	if err != nil {
		return result, err
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	var m ty.Message
	for scanner.Scan() {
		line++
		if err := json.Unmarshal(scanner.Bytes(), &m); err != nil {
			return result, errors.Join(fmt.Errorf("file: %s:%d", fileName, line), err)
		}

		isMatching := true
		if len(filters) > 0 {
			isMatching = lo.EveryBy(filters, func(filter filterFunc) bool {
				return filter(&m)
			})
		}

		if isMatching {
			result = append(result, m)
			count++
		}
		if count >= limit {
			return result, nil
		}
	}
	return result, nil
}
