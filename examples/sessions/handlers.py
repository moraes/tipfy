from tipfy import local, redirect, request, RequestHandler, Response, url_for
from tipfy.ext.session import SessionMiddleware, SessionMixin


class BasicSessionHandler(RequestHandler, SessionMixin):
    """A very basic session example."""
    # This list enables middleware for the handler.
    middleware = [SessionMiddleware]

    def get(self, **kwargs):
        # Check if a key is set in session.
        value = self.session.get('foo', None)
        if value:
            # Add the session value to our response.
            html = 'Session has a value stored for "foo": %s' % value
            html += '<br><a href="%s">Delete the session</a>' % url_for(
                'sessions/delete', redirect=request.url)
        else:
            html = 'Session was not set!'
            # Set a value in the session, like in a dictionary.
            self.session['foo'] = 'bar'

        return Response(html, mimetype='text/html')


class ShoppingCartHandler(RequestHandler, SessionMixin):
    # This list enables middleware for the handler.
    middleware = [SessionMiddleware]

    def get(self, **kwargs):
        # Add product to session if a 'add-product' is in GET.
        to_add = request.args.get('add-product', None)
        if to_add is not None:
            self.session.setdefault('products', []).append(to_add)

        # Remove product from session if a 'remove-product' is in GET.
        to_remove = request.args.get('remove-product', None)
        if to_remove is not None:
            self.session.setdefault('products', [])
            try:
                index = self.session['products'].index(to_remove)
                self.session['products'].pop(index)
            except ValueError:
                # Name wasn't in the list.
                pass

        # Get products from session.
        products = self.session.get('products', None)

        if products:
            html = 'Products in cart: ' + ', '.join(products)
            html += '<br><a href="%s">Clear the cart</a>' % url_for(
                'sessions/delete', redirect=url_for('sessions/cart'))
        else:
            html = 'The cart is empty.'

        return Response(html, mimetype='text/html')


class DeleteSessionHandler(RequestHandler, SessionMixin):
    """A handler that deletes current session and redirects back."""
    # This list enables middleware for the handler.
    middleware = [SessionMiddleware]

    def get(self, **kwargs):
        # Delete the current session.
        # You can also call self.session.clear() to make it empty instead
        # of deleting the cookie.
        local.session_store.delete_session()

        # Redirect back.
        return redirect(request.args.get('redirect', url_for('home')))
