# PyBot

This is my first telegram bot written in Python

## Commands

```
/bug                - Link to create issue on github
/db <SQL query>     - Manage your database (Only for admins)
/info               - Information about this bot
/ping               - Show usage of pinger command wich allow to
                    + add ping phrases for user who call this command
/w <City>           - Short form of /w
/weather <City>     - Weather in a city for now, today and tommorow
/wset <City>        - Set default city for /weather
/crypto             - Crypto-currency exchange rate
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
telegram:
  mode: Polling # or Webhook
  webhook_port: 30222
  webhook_url: https://example.com/{}
  # Use this if you want to run with webhook not in docker
  listen_ip: 0.0.0.0 # Your IP
database:
  host: data/pybot.db
admins:
  - Username1
  - Username2
```

Then just launch the bot

```bash
./bot/main.py
```

### Starting into a docker container

In order to build and create a docker container, `docker-compose` must be installed in your system

```bash
docker-compose up --build
```


## How to manage database

If you want that your bot triggers on a some type of messages, there some options here.

### Simple trigger

If you want a simple trigger on a message responding with your specified string

```sql
/db INSERT INTO answers(match,string) VALUES("hello!", "Hi!")
Cuttlerat: Hello!
Cutltebot: Hi!
```

### Ping
#### Add it into database

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
/db INSERT INTO ping_exclude(match) VALUES("except")
Cuttlerat: ping all except kosc
Cuttlebot: @Cuttlerat
```

#### Add with /ping command

This command setting notifications for users.
When you will send a message with a match which in `ping_phrases` table and with match of user, bot will reply on your message with `@username` in his reply and that user will get a notification even if he disabled them

Example:
```
> Ping CuttleRat
< @CuttleRat
```

Ping command is different for admins and common users


##### Admin

```
Usage: 
/ping @username <word>
/ping show <username>
/ping all
/ping delete username <word>
```

Examples:  
`/ping @username match` - Add a ping for @username with match  
`/ping show @username` - Show all matches of this user in this chat  
`/ping show all` - Show all mathces for all users in this chat  
`/ping delete @username match` - Delete a match for this user if it exists  

For add and delete commands you also can use multiple usernames at once, example:
`/ping @user_1 @user_2 @user_3 match`  
`/ping delete @user_1 @user_2 @user_3 match`  

You can delete all matches for user:
`/ping delete @username all`

##### Common user

```
Usage: 
/ping <word>
/ping show <username>
/ping me
/ping delete <word>
```

Examples:  
`/ping match` - Add a match for you. You can have only 10 matches, or more if an administrator will add it for you  
`/ping show @user_1` - Show all matches for user_1  
`/ping me` - Show all yours matches  
`/ping delete match` - Delete a match  


**And is it! Enjoy your bot!**
