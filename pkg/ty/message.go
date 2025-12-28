package ty

import "time"

type PlatformID string
type MessageTargetType string
type UserID string
type GroupID string
type Meta map[string]any

const (
	PlatformIDSkype    PlatformID = "skype"
	PlatformIDICQ      PlatformID = "icq"
	PlatformIDIRC      PlatformID = "irc"
	PlatformIDSMS      PlatformID = "sms"
	PlatformIDJabber   PlatformID = "jabber"
	PlatformIDMSN      PlatformID = "msn"
	PlatformIDYahoo    PlatformID = "yahoo"
	PlatformIDGoogle   PlatformID = "google"
	PlatformIDTelegram PlatformID = "telegram"

	MessageTargetTypeGroup MessageTargetType = "group"
	MessageTargetTypeUser  MessageTargetType = "user"
)

type Platform struct {
	ID             string     `json:"id"`
	Platform       PlatformID `json:"platform"`
	Name           string     `json:"name"`
	AvatarFileName string     `json:"avatar"`
	Meta           Meta       `json:"meta"`
}

type Contact struct {
	Name      string     `json:"name"`
	Platforms []Platform `json:"platforms"`
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
	Platform    PlatformID    `json:"platform"`
	From        UserID        `json:"from"`
	To          MessageTarget `json:"to"`
	Text        string        `json:"text"`
	Raw         any           `json:"raw,omitempty"`
	Attachments []Attachment  `json:"attachments,omitempty"`
	Meta        Meta          `json:"meta,omitempty"`
}