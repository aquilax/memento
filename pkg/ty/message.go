package ty

import "time"

type Platform string
type MessageTargetType string
type UserID string
type GroupID string
type Meta map[string]any

const (
	PlatformSkype  Platform = "skype"
	PlatformICQ    Platform = "icq"
	PlatformIRC    Platform = "irc"
	PlatformSMS    Platform = "sms"
	PlatformJabber Platform = "jabber"
	PlatformMSN    Platform = "msn"
	PlatformYahoo  Platform = "yahoo"
	PlatformGoogle Platform = "google"

	MessageTargetTypeGroup MessageTargetType = "group"
	MessageTargetTypeUser  MessageTargetType = "user"
)

type PlatformID struct {
	ID             string   `json:"id"`
	Platform       Platform `json:"platform"`
	AvatarFileName string   `json:"avatar"`
	Meta           Meta     `json:"meta"`
}

type Contact struct {
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
	Timestamp   time.Time     `json:"ts"`
	Platform    Platform      `json:"platform"`
	From        UserID        `json:"from"`
	To          MessageTarget `json:"to"`
	Text        string        `json:"text"`
	Raw         any           `json:"raw,omitempty"`
	Attachments []Attachment  `json:"attachments,omitempty"`
	Meta        Meta          `json:"meta,omitempty"`
}
