from tipfy import HTTPException
from tipfy.ext.jinja2 import render_response


class ExceptionMiddleware(object):
    def handle_exception(self, e, handler=None):
        if isinstance(e, HTTPException):
            # Get the HTTP error code to render the correspondent template:
            # 404.html, 500.html etc.
            code = e.code
        else:
            code = 500

        # Render the template.
        response = render_response(str(code) + '.html')
        response.status_code = code
        return response
