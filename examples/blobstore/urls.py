from tipfy import Rule

def get_rules():
    rules = [
        Rule('/', endpoint='home', handler='handlers.MainHandler'),
        Rule('/upload', endpoint='blobstore/upload', handler='handlers.UploadHandler'),
        Rule('/serve/<resource>', endpoint='blobstore/serve', handler='handlers.ServeHandler'),
    ]

    return rules
