# PyBot

This is my first telegram bot written in Python

## Commands

```
/weather <City>     - Weather in a city for now, today and tommorow
/w <City>           - Short form of /w
/info               - Information about this bot
/wset <City>        - Set default city for /weather
/ibash <Number>     - Random quote from ibash.org.ru
/loglist <Number>   - Random quote from loglist.net
/cat <Number>       - Random cat photo from Tumbler
/dog <Number>       - Random dog photo from dog.ceo
/ping               - Show usage of pinger command wich allow to
                    + add ping phrases for user who call this command
/db <SQL query>     - Manage your database (Only for admins)
```

## Starting

```bash
git clone https://github.com/Cuttlerat/pybot.git
cd pybot
```

Add your telegram username, tokens, and database path into `./tokens/tokens.py` file
```python
BOT_TOKEN = '<YOUR TOKEN>'
WEATHER_TOKEN = '<YOUR TOKEN>'
DATABASE_HOST = 'data/pybot.db'
ADMINS = [ 'YOUR TELEGRAM USERNAME WITHOUT @' ]
MODE = 'Webhook' # Or Polling
WEBHOOK_PORT = 30222
WEBHOOK_URL = "https://example.com/{}".format(BOT_TOKEN)
# Uncomment this if you want to run with webhook not in docker
# LISTEN_IP = "<your ip>"
```

Then just launch the bot

```bash
./pybot.py
```

### Starting into a docker container

In order to build and create a docker container, `docker-compose` must be installed in your system

```bash
docker-compose up --build pybot
```

You can get a weather token here: http://openweathermap.org/ <br>
Register your bot here: https://t.me/BotFather

## How to manage database

If you want that your bot triggers on a some type of messages, there some options here.

### Google

If you want that your bot triggers on a messages like this
```
Cuttlerat: What is Jenkins?
Cuttlebot: https://www.google.ru/search?q=Jenkins
```

You will need to add a note in your database like this:

```sql
/db INSERT INTO google(match) VALUES("what is")
```

All matches must be in a low case! It's important (I will do something with it later)

If you don't want any word to trigger this function

```sql
/db INSERT INTO google_ignore(ignore) VALUES("Jenkins")
Cuttlerat: What is Jenkins?
*no answer*
```

### Simple trigger

If you want a simple trigger on a message responding with your specified string

```sql
/db INSERT INTO answers(match,string) VALUES("hello!", "Hi!")
Cuttlerat: Hello!
Cutltebot: Hi!
```

### Ping

You also can use the `/ping` command for this, and so all the others (besides the administrator) can use this to add trigers but not more than 10

If you want to summon someone with just mentioning of his name or nickname

```sql
/db INSERT INTO pingers(username,match) VALUES("Cuttlerat", "rat")
Cuttlerat: rat!
*nothing*
```

Why? Because we didn't set a ping phrase yet

```sql
/db INSERT INTO ping_phrases(phrase) VALUES("ping")
Cuttlerat: ping rat
Cuttlebot: @Cuttlerat
```

There is a little trick to summon all persons from the pingers table

```sql
/db INSERT INTO pingers(username,match) VALUES("hotkosc", "kosc")
/db INSERT INTO pingers(username,match) VALUES("EVERYONE GET IN HERE", "all")
Cuttlerat: ping all
Cuttlebot: @Cuttlerat @hotkosc
```

But what if you want to call everyone except one guy?

You will need to add a ping exclude phrase

```sql
/db INSERT INTO ping_exclude(match) VALUES("excpet")
Cuttlerat: ping all except kosc
Cuttlebot: @Cuttlerat
```

And is it! Enjoy your bot!
