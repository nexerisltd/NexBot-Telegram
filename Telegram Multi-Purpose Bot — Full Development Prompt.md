You are a senior Telegram Bot architect and full-stack developer.

I want you to help me build a production-ready, modular, multi-purpose Telegram bot from scratch. Do NOT just give me code. Guide me through the entire development process step-by-step, explain important decisions, create the project structure, write the complete code, and help me test and deploy it.

## 1. MAIN IDEA

I want ONE Telegram bot that can be added to multiple Telegram Groups and Channels.

The bot must NOT be hardcoded for one specific group/channel.

Every Group/Channel where the bot is installed must have its own independent configuration stored in a database.

For example:

Bot is added to:

- Group A
- Group B
- Channel A
- Channel B

Each one can have completely different settings, welcome messages, images, buttons, features, etc.

The bot should dynamically detect the current chat/channel name and user information.

Example:

"Welcome @username to {chat_name}!"

Do NOT hardcode any specific community/channel name.

---

# 2. PRIMARY FEATURE — GREETINGS / WELCOME SYSTEM

When a new user joins a supported Telegram Group, the bot should automatically send a customizable welcome message.

Example:

Welcome @username to {chat_name}! 👋

We're glad to have you here.

The message must be configurable by the administrators of that specific Group.

## Supported dynamic variables

Design a clean placeholder system such as:

{user}
{username}
{first_name}
{last_name}
{user_id}
{chat_name}
{chat_id}

Example custom message:

"Welcome {first_name} (@{username}) to {chat_name}! 👋

Please read our rules before participating."

The system should safely handle users who do not have a username.

---

# 3. WELCOME MESSAGE CUSTOMIZATION

Admins should be able to configure:

- Welcome text
- Formatting
- Image/photo
- Buttons
- Multiple buttons
- URL buttons
- Optional inline keyboard
- Enable/disable welcome system
- Delete previous welcome message after X seconds (optional feature)
- Preview welcome message before saving

The welcome message should support Telegram-supported formatting such as MarkdownV2 or HTML, but implement it safely so malformed formatting does not crash the bot.

Example:

[📜 Rules] [🌐 Website]

[📚 Resources]

The admin should be able to configure these without modifying source code.

---

# 4. CHANNEL SUPPORT

The bot may also be added to Telegram Channels.

Important:

Clearly explain what Telegram permits for bots in Groups vs Channels.

Do NOT assume that a normal "new member joined" event works identically in Channels.

If Telegram does not provide a particular event or permission in Channels, explain the limitation and design the closest legitimate solution.

Do not use unofficial APIs, scraping, user-account automation, or methods that violate Telegram's platform rules.

---

# 5. MULTI-CHAT CONFIGURATION

This is extremely important.

Every chat must have its own configuration.

Example database concept:

Chat A:

welcome_enabled = true
welcome_message = "Welcome..."
welcome_image = ...
buttons = ...

Chat B:

welcome_enabled = false

Chat C:

welcome_enabled = true
welcome_message = completely different

The configuration of one chat must NEVER affect another chat.

Use Telegram chat_id as the primary identifier.

Support:

- Group
- Supergroup
- Channel where applicable

---

# 6. ADMIN CONTROL

Only authorized administrators of a Group/Channel should be able to modify that chat's configuration.

The bot must verify Telegram administrator permissions before allowing configuration commands.

For example:

/settings
/welcome
/setwelcome
/preview
/help
/info

Do NOT rely only on a username or user ID stored in the database for authorization.

Whenever appropriate, verify the user's current Telegram admin status using Telegram's API.

---

# 7. SETTINGS UI

I want the bot to have a clean interactive settings system using Telegram inline keyboards.

For example:

⚙️ Bot Settings

[👋 Greetings]
[🆘 Help]
[ℹ️ Info]
[🖼 Welcome Media]
[🔘 Buttons]
[🛡 Moderation]
[⚙️ General]

When an admin selects a feature, show its configuration options.

Example:

👋 Greetings

Status: ✅ Enabled

[Enable]
[Disable]
[✏️ Edit Message]
[🖼 Change Image]
[🔘 Manage Buttons]
[👀 Preview]

Make the UX simple enough for a non-technical Telegram admin.

---

# 8. HELP SYSTEM

Create a /help command.

It should show available commands depending on the user's permissions.

Normal user:

/start
/help
/info

Admin:

/settings
/welcome
/preview
...

The help system should be modular so future features can automatically register their commands.

---

# 9. INFO SYSTEM

Create an /info feature.

Depending on context, it may show:

User information:
- First name
- Username
- User ID

Chat information:
- Chat name
- Chat ID
- Chat type

Do not expose sensitive information unnecessarily.

---

# 10. MODULAR ARCHITECTURE

I plan to add many more features later.

Therefore, DO NOT create one giant bot.py file.

Use a clean modular architecture.

For example:

bot/
├── app/
├── handlers/
├── features/
│   ├── greetings/
│   ├── help/
│   ├── info/
│   └── moderation/
├── database/
├── services/
├── keyboards/
├── utils/
├── config/
└── main.py

You may improve this structure if you have a better architecture.

Explain why you chose the architecture.

Each feature should be independently maintainable.

---

# 11. DATABASE

Use a proper database rather than JSON files for production.

Prefer a free/low-cost solution suitable for a small-to-medium Telegram bot.

Evaluate appropriate options such as:

- PostgreSQL
- Supabase PostgreSQL
- SQLite for local development

If using PostgreSQL/Supabase, explain the setup from zero.

Design proper tables for:

- chats
- chat_settings
- admins if necessary
- welcome configurations
- buttons
- custom commands
- future feature configurations

Avoid unnecessary duplication.

Provide the complete SQL schema/migrations.

---

# 12. TECH STACK

Choose a stable and beginner-friendly production stack.

My preference is Python unless you have a strong reason to recommend another language.

For Telegram framework, evaluate a modern maintained library such as:

python-telegram-bot

or another suitable maintained framework.

Before choosing, explain:

- Why this framework
- Current compatibility
- Async support
- Telegram Bot API compatibility
- Hosting compatibility

Do not use abandoned libraries.

---

# 13. SECURITY

Security is very important.

Implement:

- Environment variables for BOT_TOKEN
- Never hardcode secrets
- Proper admin authorization
- Input validation
- Safe callback query handling
- Database parameterization/ORM
- Rate limiting where useful
- Error handling
- Logging
- Protection against malicious formatting/input
- Protection against unauthorized configuration changes

Never ask me to paste my real bot token into source code.

Use:

.env

Example:

BOT_TOKEN=your_token_here
DATABASE_URL=your_database_url_here

Also create:

.env.example

---

# 14. ERROR HANDLING

The bot must not crash because of:

- Invalid user input
- Deleted messages
- Missing username
- Invalid formatting
- Telegram API errors
- Permission errors
- Database connection problems
- Invalid callback queries

Create centralized error handling and useful logging.

---

# 15. CONFIGURATION FLOW

Design a proper admin workflow.

Example:

Admin sends:

/settings

Bot checks:

1. Is this a supported chat?
2. Is the user an admin?
3. If not → deny access.
4. If yes → show settings.

Admin selects:

Greetings → Enable → Edit Message

Bot asks:

"Send the new welcome message."

Admin sends message.

Bot previews it.

Admin chooses:

[✅ Save]
[❌ Cancel]

Then save it to database.

Build this as a reliable conversation/state flow.

---

# 16. MEDIA SUPPORT

The welcome system should support optional media.

At minimum:

- No image
- Photo

Design the database so future support for:

- Video
- Animation
- Document

can be added without rewriting the entire system.

Explain how Telegram file_id should be handled and why storing Telegram file_id is preferable to downloading every image.

---

# 17. BUTTON BUILDER

Create a simple admin interface for welcome buttons.

Example:

Admin can create:

Button text:
"📜 Rules"

URL:
"https://example.com/rules"

Then:

[Save Button]

Allow multiple buttons and configurable rows.

Example:

[📜 Rules] [🌐 Website]
[📚 Resources]

Validate URLs.

---

# 18. CUSTOM COMMANDS — FUTURE-READY

Design the architecture so admins can eventually create custom commands.

Example:

/rules

Response:

"These are our community rules..."

This should be stored per-chat.

Do not necessarily implement the full custom-command system in version 1 unless it is straightforward, but make the architecture ready for it.

---

# 19. START COMMAND

Create a polished /start command.

It should explain:

- What the bot does
- Basic commands
- How admins can add/configure it
- Help command

For example:

🤖 Welcome to [Bot Name]

I can help manage greetings, information, utilities and more.

Use /help to see available commands.

Do not use a hardcoded community-specific name.

---

# 20. BOT NAME / BRANDING

Do not assume a final bot name yet.

Use a placeholder such as:

BOT_NAME

Keep branding/configuration separate from feature logic.

---

# 21. FREE DEPLOYMENT

I want to build and deploy this with as close to zero cost as realistically possible.

Compare currently viable free/low-cost hosting options.

Consider options such as:

- Render
- Railway
- Fly.io
- Koyeb
- Cloudflare Workers if technically appropriate
- Python-compatible alternatives

Do NOT blindly recommend a service.

Check current free-tier availability/limitations before recommending one.

Explain:

- Sleep behavior
- Runtime limitations
- Database availability
- Environment variables
- Deployment method
- Whether polling or webhook is better

If a "free" service is no longer actually free, clearly say so.

---

# 22. LOCAL DEVELOPMENT

Give me exact setup instructions for Windows.

Assume I am starting from an empty folder.

Guide me through:

1. Installing Python
2. Creating project folder
3. Creating virtual environment
4. Installing dependencies
5. Creating files
6. Creating .env
7. Creating database
8. Running bot
9. Adding bot to a test group
10. Giving required permissions
11. Testing every feature

Provide exact commands.

---

# 23. BOTFATHER SETUP

Explain the complete BotFather setup.

Include:

/newbot

Bot username requirements.

Explain which BotFather settings matter.

Also explain Telegram privacy mode and whether it needs to be changed for this bot.

Do not ask me to expose my token publicly.

---

# 24. TESTING

Create a proper test checklist.

Test:

### Greetings
- New user joins
- Username exists
- Username doesn't exist
- Welcome disabled
- Custom message
- Dynamic variables
- Image
- Buttons
- Invalid URL

### Permissions
- Admin
- Non-admin
- Bot itself
- Multiple admins

### Multi-chat
- Group A settings
- Group B settings
- Verify they don't interfere

### Errors
- Invalid input
- Telegram API error
- Database unavailable
- Deleted message

---

# 25. FUTURE FEATURES

Design the system so I can later add:

- Moderation
- Anti-spam
- Warn system
- Mute
- Ban
- Auto-delete
- Rules
- Custom commands
- Scheduled messages
- Auto announcements
- Logging
- Join verification
- Captcha
- Statistics
- User management
- Role-based admin settings
- Broadcast system
- Web dashboard

Do not implement dangerous or abusive automation.

---

# 26. DEVELOPMENT METHOD

IMPORTANT:

Do NOT dump the entire project into one huge response without explaining it.

Work with me step-by-step.

First provide:

1. Final architecture
2. Recommended tech stack
3. Feature roadmap
4. Database design
5. Project structure
6. Setup prerequisites

Then start implementation.

For every implementation step:

- Tell me exactly which file to create/edit
- Give the COMPLETE content of that file
- Explain where it belongs
- Give the command to run/test it
- Explain expected output
- Tell me what to do if I get an error

When modifying an existing file, provide the complete updated file unless the change is extremely small and clearly identifiable.

Never use pseudo-code where production code is expected.

Never leave:

"implement this yourself"

or:

"add your code here"

Use complete working code.

---

# 27. IMPORTANT DEVELOPMENT RULES

Follow these rules throughout the project:

- Do not hardcode a specific Telegram group/channel.
- Do not hardcode admin usernames.
- Use chat_id-based configuration.
- Use database persistence.
- Keep features modular.
- Keep secrets in environment variables.
- Use official Telegram Bot API functionality.
- Do not scrape Telegram.
- Do not use Telegram user accounts as bots.
- Do not bypass Telegram restrictions.
- Do not use unofficial APIs to circumvent limitations.
- Follow Telegram's Bot API rules.
- Prefer maintainability over unnecessarily complex code.
- Keep the UI/UX polished.
- Use clear naming conventions.
- Add comments where they actually help.
- Avoid overengineering version 1.

---

# 28. IMPORTANT — CURRENT INFORMATION

For anything that may have changed recently, such as:

- Telegram Bot API behavior
- python-telegram-bot API
- Telegram permissions
- Hosting free tiers
- Supabase free tier
- Render/Railway/Koyeb policies

you MUST verify current information using reliable up-to-date web sources before giving me instructions.

Do not rely on outdated knowledge.

---

# 29. FINAL GOAL

At the end, I should have a fully working Telegram bot that:

✅ Works in multiple Groups  
✅ Can support Channels where Telegram permits  
✅ Has independent settings per chat  
✅ Has customizable welcome messages  
✅ Supports dynamic user/chat variables  
✅ Supports images  
✅ Supports buttons  
✅ Has /start  
✅ Has /help  
✅ Has /info  
✅ Has /settings  
✅ Has admin-only configuration  
✅ Uses a real database  
✅ Is modular  
✅ Is secure  
✅ Can be extended with many future features  
✅ Can be deployed with minimal/no cost where realistically possible

Most importantly:

I am not asking for just a code snippet.

I want you to act as my technical mentor + developer and guide me from ZERO → fully deployed production-ready bot.

Start by giving me the architecture, recommended stack, database schema, folder structure, development roadmap, and prerequisites. Then wait for my confirmation before moving to the first implementation step.