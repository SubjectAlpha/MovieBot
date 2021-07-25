import os, random, queuebot
from discord.ext.commands import Bot

import queuebot_helpers as helpers

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

#invite link https://discord.com/oauth2/authorize?client_id=858789129848225792&permissions=27712&scope=bot

'''
TODO:
Improve rating system, be allowed to vote on different movies
-$vote listall_pos ?
'''

bot = Bot(command_prefix='$')

cred = credentials.Certificate("fbase_auth.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

#Add a movie based on IMDb link
@bot.command("add", help = "$add IMDb_link to add a movie to this servers queue.")
async def add_to_list(context, link):
  if helpers.validate_imdb_url(link):
    imdb_id = link.split("/")[4]
    details = helpers.get_movie_details(link)
    current_queue = helpers.get_movie_queue(db, context.guild.id)
    if not any(x.imdb_id == imdb_id for x in current_queue.Movies):
      doc_ref = db.collection("MovieQueue").document()
      doc_ref.set(queuebot.Movie(doc_ref.id, imdb_id, context.guild.id, context.message.author.id, link, helpers.get_nowf(),details["title"], f"{details['rating']}/10", False).__dict__)
      await context.message.add_reaction("👌")
    else:
      await context.reply("This movie is already on the queue")
  else:
    await context.reply("You must submit an IMDb link")

#List all movies in current queue, and get info from IMDb about them.
@bot.command("list", help="$list count to display the list up to that count default=25")
async def get_movie_list_message(context, cnt=25):
  current_queue = helpers.get_movie_queue(db, context.guild.id, False)
  queue_msg = ""
  pos = 1
  await context.message.add_reaction("👌")
  
  for movie in current_queue.Movies[:cnt]:
    queue_msg += f"{movie.title} - {movie.rating} - Position: {str(pos)}\n"
    pos += 1
  
  await helpers.send_queued_msg(context, "Current Queue:\n" + queue_msg)

@bot.command("listall")
async def get_all_movies_message(context):
  current_queue = helpers.get_movie_queue(db, context.guild.id)
  queue_msg = ""
  pos = 1
  await context.message.add_reaction("👌")

  current_queue.Movies.sort(key = lambda x: x.viewed, reverse=False)

  for movie in current_queue.Movies:
    queue_msg += f"{movie.title} - {movie.rating} - Viewed: {movie.viewed} - Position: {str(pos)}\n"
    pos += 1

  await helpers.send_queued_msg(context, "Current Queue:\n" + queue_msg)

#Psuedo randomly choose a movie from the saved list.
@bot.command(name="random", help="$random to randomly choose a movie from this server's queue to nominate")
async def pick_random(context):
  current_queue = helpers.get_movie_queue(db, context.guild.id, False)
  pick = random.randint(0, len(current_queue)-1)
  movie = current_queue[pick]

  await context.reply(f"You should watch: {movie.title} Rating: {movie.rating}")

#Remove a movie from the list based on its current queue position.
@bot.command(name="watched", help="$watched queue_position to mark a movie as watched")
async def mark_movie(context, movie_position):
  movie_position = int(movie_position)
  current_queue = helpers.get_movie_queue(db, context.guild.id, False)
  if current_queue.Movies[movie_position - 1].added_by == context.message.author.id or helpers.check_permission(context):
    db.collection("MovieQueue").document(current_queue.Movies[movie_position - 1].id).set({'viewed': True}, merge=True)

    await context.message.add_reaction("👌")
  else:
    await context.reply("You can only remove movies you've added")

@bot.command(name="remove")
async def remove_movie(context, movie_position):
  movie_position = int(movie_position)
  current_queue = helpers.get_movie_queue(db, context.guild.id, True)
  if current_queue.Movies[movie_position - 1].added_by == context.message.author.id or helpers.check_permission(context):
    db.collection("MovieQueue").document(current_queue.Movies[movie_position - 1].id).delete()

    await context.message.add_reaction("👌")
  else:
    await context.reply("You can only remove movies you've added")

#Nominate a movie for watching
@bot.command(name="nominate", help="$nominate queue_position to nominate a movie of your choice.")
async def nominate_movie(context, movie_position):
  movie_position = int(movie_position)
  current_queue = helpers.get_movie_queue(db, context.guild.id, False)
  movie = current_queue.Movies[movie_position - 1]

  await context.reply(f"{movie.title} Rating: {movie.rating} has been nominated. Please vote with :thumbsup: or :thumbsdown:")

#Get the link for a selected movie
@bot.command(name="link", help="$link queue_position to get the link for the movie at that position in queue.")
async def get_link(context, movie_position):
  movie_position = int(movie_position)
  current_queue = helpers.get_movie_queue(db, context.guild.id, False)
  movie = current_queue.Movies[movie_position - 1]
  print(movie.__dict__)
  await context.reply(f"{movie.url}")

@bot.command(name="top")
async def list_top_rated(context, amount=10):
  current_queue = helpers.get_movie_queue(db, context.guild.id)
  await context.message.add_reaction("👌")
  list_msg = ""
  movies = []

  for movie in current_queue.Movies:
    rating = helpers.get_movie_rating(db, context.guild.id, movie.id)
    movies.append({"movie": helpers.get_movie(db, rating['id']), "rating": rating['rating']})

  movies.sort(key=lambda x: x['rating'], reverse=True)
  movies = movies[:amount]

  for movie in movies:
    list_msg += f"{movie['movie'].title} - Votes: {movie['rating']} Submitter: <@{movie['movie'].added_by}>\n"

  await helpers.send_queued_msg(context, list_msg)

#Clear channel messages
@bot.command(name="cls")
async def clear_messages(context):
  if helpers.check_permission(context):
    await context.channel.purge(limit=120)
  else:
    await context.reply("You must be in group 'Mods' or 'Admins' or 'Curator'")

'''
Keep this for any new db changes
@bot.command(name="update")
async def update_records(context):
  if helpers.check_permission(context):
    docs = db.collection("MovieQueue").where("server_id", "==", context.guild.id).stream()
    queue = []
    for doc in docs:
      queue.append(doc.to_dict())
    for movie in queue:
     db.collection("MovieQueue").document(movie['id']).set({'viewed': False, 'points': 0}, merge=True)
'''
#Status message to know when the bot is ready.
@bot.event
async def on_ready():
  helpers.pretty_print(f'We have logged in as {bot.user}')

#Start of the voting system
@bot.event
async def on_reaction_add(reaction, user):
  if user != bot.user:
    msg = await helpers.get_message_from_reference(bot, reaction.message.reference)
    queue_pos = int(msg.content.split()[1])
    guild_id = msg.guild.id
    current_queue = helpers.get_movie_queue(db, guild_id)
    selected_movie = current_queue.Movies[queue_pos - 1]

    current_movie_doc_ref = db.collection("MovieQueue").document(selected_movie.id)

    if reaction.emoji == "👍":
      rating_ref = db.collection("Rating").document()
      
      rating_ref.set(queuebot.Rating(rating_ref.id, guild_id, current_movie_doc_ref.id, msg.author.id, True).__dict__)
    elif reaction.emoji == "👎":
      rating_ref = db.collection("Rating").document()
      rating_ref.set(queuebot.Rating(rating_ref.id, guild_id, current_movie_doc_ref.id, False).__dict__)
  
bot.run(os.environ['BOT_TOKEN'])
