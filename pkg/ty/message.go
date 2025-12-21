package ty

import "time"

type Platform string
type MessageTargetType string
type UserID string
type GroupID string

const (
	PlatformSkype Platform = "skype"
	PlatformICQ   Platform = "icq"
	PlatformIRC   Platform = "irc"
	PlatformSMS   Platform = "sms"

	MessageTargetTypeGroup MessageTargetType = "group"
	MessageTargetTypeUser  MessageTargetType = "user"
)

type PlatformID struct {
	ID             string            `json:"id"`
	Platform       Platform          `json:"platform"`
	AvatarFileName string            `json:"avatar"`
	Meta           map[string]string `json:"meta"`
}

type User struct {
	Name        string       `json:"name"`
	PlatformIDs []PlatformID `json:"platform_ids"`
}

type MessageTarget struct {
	MessageTargetType MessageTargetType `json:"type"`
	UserID            *UserID           `json:"user_id,omitempty"`
	GroupID           *GroupID          `json:"group_id,omitempty"`
}

type Attachment struct {
	FileName string `json:"file_name"`
	MimeType string `json:"mime_type"`
}

type Message struct {
	Platform    Platform      `json:"platform,"`
	Timestamp   time.Time     `json:"ts,"`
	From        UserID        `json:"from,"`
	To          MessageTarget `json:"to,"`
	Text        string        `json:"text,"`
	Raw         any           `json:"raw,"`
	Attachments []Attachment  `json:"attachments"`
}
