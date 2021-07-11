class Queue:
  def __init__(self):
    self.Movies = []

  def from_collection(self, collection):
    for doc in collection:
      doc = doc.to_dict()
      self.Movies.append(Movie(doc['id'], doc['imdb_id'], doc['server_id'], doc['added_by'], doc['url'], doc['date_added'], doc['title'], doc['rating'], doc['viewed']))
    
    self.Movies.sort(key=lambda x: x.date_added)


class Movie:
  def __init__(self, id=0, imdb_id=0, server_id=0, added_by=0, url="", date_added="", title="", rating="", viewed=True):
    self.id = id
    self.imdb_id = imdb_id
    self.server_id = server_id 
    self.url = url
    self.added_by = added_by
    self.date_added = date_added
    self.title = title
    self.rating = rating
    self.viewed = viewed

  def from_dict(self, obj):
    self.id = obj['id']
    self.imdb_id = obj['imdb_id']
    self.server_id = obj['server_id']
    self.url = obj['url']
    self.added_by = obj['added_by']
    self.date_added = obj['date_added']
    self.title = obj['title']
    self.rating = obj['rating']
    self.viewed = obj['viewed']

class Rating:
  def __init__(self, id=0, server_id=0, movie_id=0, added_by=0, positive=False):
    self.id = id
    self.server_id = server_id
    self.movie_id = movie_id
    self.added_by = added_by
    self.positive = positive

  def from_dict(self, obj):
    self.id = obj['id']
    self.server_id = obj['server_id']
    self.movie_id = obj['movie_id']
    self.added_by = obj['added_by']
    self.positive = obj['positive']

    print(self)
