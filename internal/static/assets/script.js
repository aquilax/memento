let currentContactId = null;
let nextCursor = null;
let isLoading = false;

const viewport = document.getElementById("message-viewport");

// Scroll event for "Infinite Loading"
viewport.addEventListener("scroll", () => {
  // If we scroll to the top and have a cursor, load more
  if (viewport.scrollTop === 0 && nextCursor && !isLoading) {
    fetchMessages(currentContactId, nextCursor);
  }
});

async function fetchMessages(contactId, cursor = null) {
  if (isLoading) return;
  isLoading = true;

  const statusEl = document.getElementById("load-status");
  statusEl.classList.remove("hidden");

  try {
    const url = `/api/messages?contact_id=${contactId}${
      cursor ? `&cursor=${cursor}` : ""
    }`;
    const response = await fetch(url);
    const { messages, next_cursor } = await response.json();

    const list = document.getElementById("message-list");

    // Record height before adding elements to maintain scroll position
    const oldHeight = list.scrollHeight;

    messages.forEach((msg) => {
      const msgEl = document.createElement("div");
      msgEl.className = `message ${
        msg.from === contactId ? "received" : "sent"
      }`;
      msgEl.innerHTML = `
                ${msg.text}
                <span class="timestamp">${msg.ts}</span>
            `;
      // Add to top of list
      list.append(msgEl);
    });

    nextCursor = next_cursor;

    // Adjust scroll so the user doesn't "lose" their place when new items load
    if (cursor) {
      viewport.scrollTop = list.scrollHeight - oldHeight;
    } else {
      // First load: scroll to bottom
      viewport.scrollTop = viewport.scrollHeight;
    }
  } finally {
    isLoading = false;
    statusEl.classList.add("hidden");
  }
}

async function fetchContacts() {
  try {
    const response = await fetch("/api/contacts");
    const contacts = await response.json(); // Array of Contact objects

    const list = document.getElementById("contact-list");
    list.innerHTML = ""; // Clear loading state

    contacts.forEach((contact) => {
      // Get the first platform ID as the primary reference
      const primaryPlatform = contact.platform_ids[0] || {};
      const avatarUrl = primaryPlatform.avatar
        ? `/uploads/avatars/${primaryPlatform.avatar}`
        : "/assets/default-avatar.png";

      const li = document.createElement("li");
      li.className = "contact-item";

      // We use the first PlatformID's string ID for message filtering
      li.dataset.contactId = primaryPlatform.id;

      li.innerHTML = `
                <!--
                <img src="${avatarUrl}" class="avatar" alt="${contact.name}">
                -->
                <div class="contact-info">
                    <div class="contact-name">${contact.name}</div>
                    <div class="contact-meta">${
                      primaryPlatform.platform || ""
                    }</div>
                </div>
            `;

      li.addEventListener("click", () => {
        // Pass the primary ID to the message fetcher
        selectContact(primaryPlatform.id, contact.name, li);
      });

      list.appendChild(li);
    });
  } catch (error) {
    console.error("Failed to load contacts:", error);
  }
}

function selectContact(id, name, element) {
  document
    .querySelectorAll(".contact-item")
    .forEach((el) => el.classList.remove("active"));
  element.classList.add("active");

  // Update global state and fetch messages
  currentContactId = id;
  document.getElementById("chat-header").textContent = name;

  // Reset message list and fetch fresh history
  document.getElementById("message-list").innerHTML = "";
  nextCursor = null;
  fetchMessages(id);
}

fetchContacts();
