goog.provide('tipfy.ui.Messages');

goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.dom.query');
goog.require('goog.events');
goog.require('goog.fx');
goog.require('goog.fx.Animation');
goog.require('goog.fx.Animation.EventType');
goog.require('goog.fx.AnimationParallelQueue');
goog.require('goog.fx.dom');
goog.require('goog.Timer');


tipfy.ui.Messages = function(container_id, opt_domHelper) {
    this.container = goog.dom.getElement(container_id);
    if(!this.container) {
        this.container = goog.dom.createDom('div', {'id': container_id});
        goog.dom.appendChild(document.body, this.container);
    }
};

tipfy.ui.Messages.prototype.LoadFromMarkup = function() {
    var _this = this;
    messages = goog.dom.query('.message', this.container);
    goog.array.map(messages, function(el) {
        _this.ShowMessage(el, el.getAttribute('life'));
    });
};

tipfy.ui.Messages.prototype.addMessages = function(messages) {
    var _this = this;
    goog.array.map(messages, function(m) { _this.addMessage(m); });
};

tipfy.ui.Messages.prototype.addMessage = function(options) {
    var msg,
        msg_class = options.level ? 'message ' + options.level : 'message';

    msg = goog.dom.createDom('div', {'class': msg_class, 'style': 'display: none;'});
    if(options.title) {
        goog.dom.appendChild(msg, goog.dom.createDom('h4', null, options.title));
    }
    if(options.body) {
        goog.dom.appendChild(msg, goog.dom.createDom('p', null, options.body));
    }
    goog.dom.appendChild(msg, goog.dom.createDom('div', {'class': 'close'}, '×'));
    goog.dom.appendChild(this.container, msg);
    this.ShowMessage(msg, options.life);
};

tipfy.ui.Messages.prototype.ShowMessage = function(el, life) {
    var _this = this,
        anim = new goog.fx.dom.FadeInAndShow(el, 100);

    if(goog.userAgent['IE']) {
        el.className += ' ie6';
    }

    life *= 1;
    if(life && goog.isNumber(life)) {
        // Add event to hide it after some time.
        goog.events.listen(anim, goog.fx.Animation.EventType.END, function() {
            this.SetTimer(el, life);
        }, false, this);
    }

    // Add event to close message on click.
    goog.array.map(goog.dom.query('.close', el), function(close_el) {
        goog.events.listen(el, goog.events.EventType.CLICK, function(e) {
            this.HideMessage(el);
        }, false, _this);
    });

    anim.play();
};

tipfy.ui.Messages.prototype.HideMessage = function(el) {
    var anim, status = goog.style.getStyle(el, 'display');
    if(status != 'none') {
        // Message is still visible, so hide it with an animation.
        anim = new goog.fx.dom.FadeOutAndHide(el, 500);
        anim.play();
    }
};

tipfy.ui.Messages.prototype.SetTimer = function(el, seconds) {
    var _this = this,
        doOnceTimer = goog.Timer.callOnce(function() {
        _this.HideMessage(el);
        doOnceTimer = null;
    }, seconds * 1000);
};
