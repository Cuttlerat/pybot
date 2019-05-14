# YOBA

Yet One Bot Assistant - just a funny telegeram bot.

## Commands

```
/issue                     - Link to create an issue on github
/bug                       - The same as /issue
/db <SQL query>            - Manage your database (Only for admins)
/info                      - Information about this bot
/ping_add [matches]        - Add casts for users. Admins can use it like this
                           + /ping_add @username1 @username2 match1 match2
/ping_add_me               - Add casts for user which can be randomly chosen in /me command
/ping_show                 - Show all casts for user
/ping_show_all             - Show all casts from DB for this chat (only for admins)
/ping_delete [matches]     - Delete matches for user. The same usage for admins as for /ping_add
/ping_delete_me            - Delete matches for user which can be used in /me
/ping_drop <Username>      - Delete all matches for user (only for admins)
/me [message]              - Delete source message and replace it with this one
                           + <Random cast for user which was added by /ping_add_me> [message]
/w <City>                  - Short form of /w
/weather <City>            - Weather in a city for now, today and tommorow
/wset <City>               - Set the default city for /weather
/crypto                    - Crypto-currency exchange rate
/mute_on                   - Turn on an auto-ban (readonly) for everyone for 5 minutes (except admins)
/mute_off                  - Turn off an auto-ban
/clash                     - Create a CoC competition (https://condingame.com)
/clash_start               - Start a CoC competition
/clash_enable              - Enable CoC notifications
/clash_disable             - Disable CoC notifications
/clash_results <clash_id>  - CoC results of a given <clash_id> game,
                           + or the last one if called without any args
```

## Starting

```bash
git clone https://github.com/Cuttlerat/pybot.git
cd pybot
```

Add your telegram username, tokens, and database path into `./bot/config/config.yaml` file
```yaml
tokens:
  tg_token: YOUR_TOKEN       # Register your bot here: https://t.me/BotFather
  weather_token: YOUR_TOKEN  # You can get a weather token here: http://openweathermap.org/
  clash_remcg: COOKIE        # You can take it from https://codingame.com cookies
  clash_remember_me: COOKIE  # You can take it from https://codingame.com cookies
  clash_cg_session: COOKIE   # You can take it from https://codingame.com cookies
  clash_secret: SECRET       # You can take it from https://codingame.com requests
telegram:
  mode: Polling # or Webhook
  webhook_port: 30222
  webhook_url: https://example.com/{}
  # Use this if you want to run with webhook not in docker
  listen_ip: 0.0.0.0 # Your IP
database:
  host: data/pybot.db
log:
  level: INFO               # Can be one of ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
admins:
  - Username1
  - Username2
```

Then just launch the bot

```bash
./bot/main.py
```

### Starting into a docker container

In order to build and create a docker container, `docker-compose` must be installed on your system

```bash
docker-compose up --build
```


## How to manage database

If you want your bot triggers on a some type of messages, there some options here.

### Simple trigger

If you want a simple trigger on a message responding with your specified string

```sql
/db INSERT INTO answers(match,string) VALUES("hello!", "Hi!")
Cuttlerat: Hello!
Cutltebot: Hi!
```

### Ping
#### Add it into database

You can also use the `/ping` command for this, others (besides admins) can use it to add trigers by themselves, but not more than 10 per user.

If you want to summon someone by mentioning his name or nickname

```sql
/db INSERT INTO pingers(username,match) VALUES("Cuttlerat", "rat")
Cuttlerat: rat!
*nothing*
```

Why it didn't work? Because we haven't set a ping phrase yet

```sql
/db INSERT INTO ping_phrases(phrase) VALUES("ping")
Cuttlerat: ping rat
Cuttlebot: @Cuttlerat
```

There is also a little trick to summon all persons from the pingers table

```sql
/db INSERT INTO pingers(username,match) VALUES("hotkosc", "kosc")
/db INSERT INTO pingers(username,match) VALUES("EVERYONE GET IN HERE", "all")
Cuttlerat: ping all
Cuttlebot: @Cuttlerat @hotkosc
```

But what if you want to call everyone except one guy?

You will need to add a ping exclude phrase

```sql
/db INSERT INTO ping_exclude(match) VALUES("except")
Cuttlerat: ping all except kosc
Cuttlebot: @Cuttlerat
```

#### Add with /ping_* commands

`/ping` command is deprecated!
Use `/ping_add`, `/ping_show`, `/ping_show_all` and `/ping_delete` instead

These commands set and delete ping phrases for users and show them the existing ones.
When you send a message with a match from `ping_phrases` table and with a match that user sets, bot will reply on your message with his `@username` in and that user will get a notification even if he disabled them for this chat.

Example:
```
> Ping CuttleRat
< @CuttleRat
```

Ping command is different for admins and common users


##### Admins usage

```
Usage:
/ping_add [@username] [match] - Add a ping for @username with match
/ping_show [@username] - Show all matches of this user in this chat
/ping_show_all - Show all mathces for all users in this chat
/ping_delete [@username] [match] - Delete a match for this user if it exists
/ping_drop [@username]` - Delete all matches for this user if it exists
```

For `/ping_add` and `/ping_delete` commands you can also use multiple usernames at once
```
/ping_add @user_1 @user_2 @user_3 match
/ping_delete @user_1 @user_2 @user_3 match
/ping_drop @user_1 @user_2 @user_3
```

##### Common user

```
Usage:
/ping_add [match] - Add a match for you. You can have only 10 matches, or more if an administrator will add it for you
/ping_show [@username] - Show all matches for @user_1
/ping_delete [match] - Delete a match
```

## Clash of code

The following commands allow you to create a new [Clash of Code](https://www.codingame.com/multiplayer/clashofcode) game and not miss any games created by someone else.

### Create a new game

```
/clash

Cuttlebot:

Clash of Code!

https://www.codingame.com/clashofcode/clash/GAME_ID

@User1 @User2 @User3

Please send /clash_disable if you don't want to receive these notifications
```

### Disable and enable notifications

```
/clash_disable

Cutlebot:

Now you won't receive any notifications about Clash of Code games
```

```
/clash_enable

Cutlebot:

You will be notified when a new game is created!
```

### Manually start the last created game

Remember that only the creator can start the game.

```
/clash_start

Cuttlebot:

The game is about to start, hurry up!

@User1 @User2 @User3
```

### Get game results

```
/clash_results <game_id>

Game id: <game_id>
Game mode: Shortest
Status: Finished

╒════╤═══════════╤═════════╤═════════╤══════════════╕
│    │ Username  │ Score   │ Time    │   Characters │
╞════╪═══════════╪═════════╪═════════╪══════════════╡
│  1 │ User1     │ 100%    │ 0:01:00 │           87 │
├────┼───────────┼─────────┼─────────┼──────────────┤
│  2 │ User2     │ 100%    │ 0:05:00 │          107 │
╘════╧═══════════╧═════════╧═════════╧══════════════╛
```

**Enjoy your bot!**

