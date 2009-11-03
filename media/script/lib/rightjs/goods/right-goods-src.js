/**
 * All the RightJS Goods project modules
 *
 * @copyright 2008-2009 Nikolay V. Nemshilov
 */

/**
 * The Event class additional functionality
 *
 * Copyright (C) 2008-2009 Nikolay V. Nemshilov aka St. <nemshilov#gma-il>
 */
Event.extend((function() {
  var old_ext = Event.ext;

return {
  /**
   * extends a native object with additional functionality
   *
   * @param Event event
   * @return Event same event but extended
   */
  ext: function(event) {
    if (!event.stop) {
      old_ext.call(Event, event);
      
      if (Event.Mouse.NAMES.includes(event.type)) {
        Event.Mouse.ext(event);
      } else if (defined(event.keyCode)){
        Event.Keyboard.ext(event);
      }
    }
    
    return event;
  },
  
  // keyboard key codes
  KEYS: {
    BACKSPACE:  8,
    TAB:        9,
    ENTER:     13,
    ESCAPE:    27,
    SPACE:     32,
    PAGE_UP:   33,
    PAGE_DOWN: 34,
    END:       35,
    HOME:      36,
    LEFT:      37,
    UP:        38,
    RIGHT:     39,
    DOWN:      40,
    INSERT:    45,
    DELETE:    46
  },
  
  // mouse button codes
  BUTTONS: (Browser.IE || Browser.Konqueror) ? {
    LEFT:   1,
    MIDDLE: 4,
    RIGHT:  2
  } : {
    LEFT:   0,
    MIDDLE: 1,
    RIGHT:  2
  }
  
}})());

Event.include({
  /**
   * constructor. pretty much plays a virtual factory, instances new events or extends
   * existing ones and always returns an event instead of void as a normal constructor
   *
   * @param mixed native Event instance or String event name
   * @param Object options
   * @return Event instance
   */
  initialize: function() {
    var args = $A(arguments), event = args.shift(), options = args.pop() || {};
    
    if (isString(event)) {
      var name = Event.cleanName(event);
      if (Event.Mouse.NAMES.includes(name)) {
        event = new Event.Mouse(name, options);
      } else if (Event.Keyboard.NAMES.includes(name)) {
        event = new Event.Keyboard(name, options);
      } else {
        event = new Event.Custom(name, options);
      }
    }
    
    return Event.ext(event);
  }
});
/**
 * presents the basic events class
 *
 * Copyright (C) 2008-2009 Nikolay V. Nemshilov aka St. <nemshilov#gma-ilc-om>
 */
Event.Base = new Class({
  extend: {
    // basic default events options
    Options: {
      bubbles:    true,
      cancelable: true,
      altKey:     false,
      ctrlKey:    false,
      shiftKey:   false,
      metaKey:    false
    }
  },
  
  /**
   * basic constructor
   *
   * NOTE: that's a virtual constructor, it returns a new object instance
   *       not the actual class instance.
   * 
   * @param String event name
   * @param Object options
   * @return Event new event
   */
  initialize: function(name, options) {
    return this.build(this.options(name, options));
  },
  
// protected

  /**
   * default building method
   *
   * the main purpose is that IE browsers share events instaciation interface
   *
   * @param Object options
   * @return Event new event
   */
  build: Browser.IE ? function(options) {
    var event = document.createEventObject();
    event.type = event.eventType = "on" + options.name;
    event.altKey = options.altKey;
    event.ctrlKey = options.ctrlKey;
    event.shiftKey = options.shiftKey;
    return event;
  } : null,
  
  /**
   * initial options parsing
   *
   * @params Sting event name
   * @params Object user options
   * @return Object clean options
   */
  options: function(name, options) {
    options = Object.merge({}, Event.Base.Options, this.Options, options);
    options.name = name;
    
    return options;
  }
});
/**
 * presents the mouse events class
 *
 * NOTE: this class generally is for an internal usage, it builds a new clean
 *       unextended mouse event.
 *       Use the Event general constructor, if you need a usual extened event.
 *
 * Copyright (C) 2008-2009 Nikolay V. Nemshilov aka St. <nemshilov#gma-ilc-om>
 */
Event.Mouse = new Class(Event.Base, {
  
  extend: {
    NAMES: $w('click middleclick rightclick dblclick mousedown mouseup mouseover mouseout mousemove'),
    
    Methods: {
      isLeftClick: function() {
        return this.which == 1;
      },

      isRightClick : function() {
        return this.which == 3;
      }
    },
    
    /**
     * proceses the event extending as if it's a mouse event
     *
     * @param Event new event
     * @return Event extended event
     */
    ext: function(event) {
      $ext(event, this.Methods, true);
            
      return event;
    }
  },
  
  // default mouse events related options
  Options: {
    pointerX: 0,
    pointerY: 0,
    button:   0
  },

// protecteds
  build: function(options) {
    var event = Browser.IE ? this.$super(options) : document.createEvent("MouseEvent");
    this[Browser.IE ? 'initIE' : 'initW3C'](event, options);
    return event;
  },
  
  options: function(name, options) {
    options = this.$super(name, options);
    options.button = Event.BUTTONS[options.name == 'rightclick' ? 'RIGHT' : options.name == 'middleclick' ? 'MIDDLE' : 'LEFT'];
    options.name   = Event.realName(options.name);
    
    return options;
  },
  
// private
  initIE: function(event, options) {
    event.clientX = options.pointerX;
    event.clientY = options.pointerY;
    event.button  = options.button;
  },
  
  initW3C: function(event, options) {
    event.initMouseEvent(options.name, options.bubbles, options.cancelable, document.defaultView,
      name == 'dblclick' ? 2 : 1, options.pointerX, options.pointerY, options.pointerX, options.pointerY,
      options.ctrlKey, options.altKey, options.shiftKey, options.metaKey, options.button, options.element
    );
  }
});

try {
  // boosting up the native events by preextending the prototype if available
  $ext(Event.parent.prototype, Event.Mouse.Methods, true);
} catch(e) {};

/**
 * presents the keyboard events class
 *
 * NOTE: this class generally is for an internal usage, it builds a new clean
 *       unextended mouse event.
 *       Use the Event general constructor, if you need a usual extened event.
 *
 * Copyright (C) 2008-2009 Nikolay V. Nemshilov aka St. <nemshilov#gma-ilc-om>
 */
Event.Keyboard = new Class(Event.Base, {
  
  extend: {
    NAMES: $w('keypress keydown keyup'),
    
    /**
     * automatically generates the key checking methods like
     * isEscape()
     * isEnter()
     * etc
     */
    Methods: {}, // generated at the end of the file
    
    /**
     * processes the event extending as a keyboard event
     *
     * @param Event before extending
     * @return Event after extending
     */
    ext: function(event) {
      $ext(event, this.Methods, true);
      
      return event;
    }
  },
  
  // default keyboard related events options
  Options: {
    keyCode:  0,
    charCode: 0
  },
  
// protected
  build: function(options) {
    var event = null;
    
    if (Browser.IE) {
      event = this.$super(options);
      this.initIE(event, options)
    } else try {
      // Gecko, WebKit, Chrome
      event = document.createEvent('KeyboardEvent');
      this['init'+(Browser.WebKit ? 'Webkit' : 'Gecko')](event, options);
    } catch(e) {
      // basically Opera
      event = document.createEvent('UIEvent');
      this.initDOM2(event, options);
    }
    
    return event;
  },
  
  initGecko: function(event, options) {
    event.initKeyEvent(options.name,
      options.bubbles, options.cancelable, document.defaultView,
      options.ctrlKey, options.altKey, options.shiftKey, options.metaKey,
      options.keyCode, options.charCode
    );
  },
  
  initWebkit: function(event, options) {
    event.initKeyboardEvent(options.name,
      options.bubbles, options.cancelable, document.defaultView,
      null, 0, options.ctrlKey, options.altKey, options.shiftKey, options.metaKey
    );
  },
  
  initDOM2: function(event, options) {
    event.initUIEvent(options.name, options.bubbles, options.cancelable, document.defaultView, 1);

    event.keyCode   = options.keyCode;
    event.charCode  = options.charCode;
    event.altKey    = options.altKey;
    event.metaKey   = options.metaKey;
    event.ctrlKey   = options.ctrlKey;
    event.shiftKey  = options.shiftKey;
  },
  
  initIE: function(event, options) {
    event.keyCode  = options.keyCode;
    event.charCode = options.charCode;
  }
});

// generates the key checking methods
(function() {
  for (var key in Event.KEYS) {
    (function(key, key_code) {
      Event.Keyboard.Methods[('is_'+key.toLowerCase()).camelize()] = function() {
        return this.keyCode == key_code;
      };
    })(key, Event.KEYS[key]);
  };
  try {
    // boosting up the native events by preextending the prototype if available
    $ext(Event.parent.prototype, Event.Keyboard.Methods, true);
  } catch(e) {};
})();

/**
 * Reassigning the element #fire method to support the native events dispatching
 *
 * @copyright 2009 Nikolay V. Nemshilov aka St.
 */
Element.addMethods({
  fire: function() {
    var args = $A(arguments), event = new Event(args.shift(), Object.merge(args.shift(), {element: this}));
    
    if (event instanceof Event.Custom) {
      (this.$listeners || []).each(function(i) {
        if (i.e == event.eventName) {
          i.f.apply(this, [event].concat(i.a).concat(args));
        }
      }, this);
    } else if (this.dispatchEvent) {
      this.dispatchEvent(event);
    } else {
      this.fireEvent(event.eventType, event);
    }
    
    return this;
  }
});

/**
 * The basic move visual effect
 *
 * @copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */
Fx.Move = new Class(Fx.Morph, {
  extend: {
    Options: Object.merge(Fx.Options, {
      duration: 'long',
      position: 'absolute' // <- defines the positions measurment principle, not the element positioning
    })
  },
  
  prepare: function(end_position) {
    return this.$super(this.getEndPosition(end_position));
  },
  
  // moved to a separated method to be able to call it from subclasses
  getEndPosition: function(end_position) {
    var position = this.element.getStyle('position'), end_style = {};
    
    if (position != 'absolute' || position != 'relative') {
      this.element.style.position = position = position == 'fixed' ? 'absolute' : 'relative';
    }
    
    if (end_position.top)  end_position.y = end_position.top.toInt();
    if (end_position.left) end_position.x = end_position.left.toInt();
    
    // adjusting the end position
    var cur_position = this.element.position();
    var par_position = this.getParentPosition();
    var rel_left     = cur_position.x - par_position.x;
    var rel_top      = cur_position.y - par_position.y;
    
    if (this.options.position == 'relative') {
      if (position == 'absolute') {
        if (defined(end_position.x)) end_position.x += cur_position.x;
        if (defined(end_position.y)) end_position.y += cur_position.x;
      } else {
        if (defined(end_position.x)) end_position.x += rel_left;
        if (defined(end_position.y)) end_position.y += rel_top;
      }
    } else if (position == 'relative') {
      if (defined(end_position.x)) end_position.x += rel_left - cur_position.x;
      if (defined(end_position.y)) end_position.y += rel_top  - cur_position.y;
    }
    
    // need this to bypass the other styles from the subclasses
    for (var key in end_position) {
      switch (key) {
        case 'top': case 'left': break;
        case 'y':   end_style.top  = end_position.y + 'px'; break;
        case 'x':   end_style.left = end_position.x + 'px'; break;
        default:    end_style[key] = end_position[key];
      }
    }
    
    return end_style;
  },
  
  getParentPosition: function() {
    Fx.Move.Dummy = Fx.Move.Dummy || new Element('div', {style: 'width:0;height:0;visibility:hidden'});
    this.element.insert(Fx.Move.Dummy, 'before');
    var position = Fx.Move.Dummy.position();
    Fx.Move.Dummy.remove();
    return position;
  }
});
/**
 * Zoom visual effect, graduately zoom and element in or out
 *
 * @copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */
Fx.Zoom = new Class(Fx.Move, {
  PROPERTIES: $w('width height lineHeight paddingTop paddingRight paddingBottom paddingLeft fontSize borderWidth'),
  
  extend: {
    Options: Object.merge(Fx.Move.Options, {
      position: 'relative', // overriding the Fx.Move default
      duration: 'normal',
      from:     'center'
    })
  },
  
  prepare: function(size, additional_styles) {
    return this.$super(this._getZoomedStyle(size, additional_styles));
  },
  
// private

  // calculates the end zoommed style
  _getZoomedStyle: function(size, additional_styles) {
    var proportion = this._getProportion(size);
    
    return Object.merge(
      this._getBasicStyle(proportion),
      this._getEndPosition(proportion),
      additional_styles || {}
    );
  },

  // calculates the zooming proportion
  _getProportion: function(size) {
    if (isHash(size)) {
      var sizes = $E('div').insertTo(
        $E('div', {style: "visibility:hidden;float:left;height:0;width:0"}).insertTo(document.body)
      ).setStyle(size).sizes();
      
      if ('height' in size) size = sizes.y / this.element.sizes().y;
      else                  size = sizes.x / this.element.sizes().x;
    } else if (isString(size)) {
      size  = size.endsWith('%') ? size.toFloat() / 100 : size.toFloat();
    }
    
    return size;
  },
  
  // getting the basic end style
  _getBasicStyle: function(proportion) {
    var style = this._getStyle(this.element, this.PROPERTIES);
    
    this._cleanStyle(style);
    
    for (var key in style) {
      if (style[key][0] > 0) {
        style[key] = (proportion * style[key][0]) + style[key][1];
      } else {
        delete(style[key]);
      }
    }
    // preventing the border disappearance
    if (style.borderWidth && style.borderWidth.toFloat() < 1) {
      style.borderWidth = '1px';
    }
    
    return style;
  },
  
  // getting the position adjustments
  _getEndPosition: function(proportion) {
    var position = {};
    var sizes    = this.element.sizes();
    var x_diff   = sizes.x * (proportion - 1);
    var y_diff   = sizes.y * (proportion - 1);
    
    switch (this.options.from.replace('-', ' ').split(' ').sort().join('_')) {
      case 'top':
        position.x = - x_diff / 2;
        break;
        
      case 'right':
        position.x = - x_diff;
        position.y = - y_diff / 2;
        break;
        
      case 'bottom':
        position.x = - x_diff / 2;
      case 'bottom_left':
        position.y = - y_diff;
        break;
        
      case 'bottom_right':
        position.y = - y_diff;
      case 'right_top':
        position.x = - x_diff;
        break;
        
      case 'center':
        position.x = - x_diff / 2;
      case 'left':
        position.y = - y_diff / 2;
        break;
        
      default: // left_top or none, do nothing, let the thing expand as is
    }
    
    return position;
  }
});
/**
 * Bounce visual effect, slightly moves an element forward and back
 *
 * @copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */
Fx.Bounce = new Class(Fx, {
  extend: {
    Options: Object.merge(Fx.Options, {
      duration:  'short',
      direction: 'top',
      value:     16 // the shake distance
    })
  },
  
  prepare: function(value) {
    value = value || this.options.value;
    
    var position = this.element.position();
    var duration = Fx.Durations[this.options.duration]     || this.options.duration;
    var move_options = {duration: duration, position: 'relative'};
    
    var key = 'y'; // top bounce by default
    
    switch (this.options.direction) {
      case 'right':
        value = -value;
      case 'left':
        key = 'x';
        break;
      case 'bottom':
        value = -value;
    }
    
    var up_pos = {}, down_pos = {};
    up_pos[key]   = -value;
    down_pos[key] = value;
    
    new Fx.Move(this.element, move_options).start(up_pos);
    new Fx.Move(this.element, move_options).start(down_pos);
    
    this.finish.bind(this).delay(1);
    
    return this;
  }
});
/**
 * run out and run in efffects
 *
 * Copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */
Fx.Run = new Class(Fx.Move, {
  extend: {
    Options: Object.merge(Fx.Move.Options, {
      direction: 'left'
    })
  },
  
  prepare: function(how) {
    var how = how || 'toggle', position = {}, dimensions = this.element.dimensions(), threshold = 80;
    
    if (how == 'out' || (how == 'toggle' && this.element.visible())) {
      if (this.options.direction == 'left') {
        position.x = -dimensions.width - threshold;
      } else {
        position.y = -dimensions.height - threshold;
      }
      this.onFinish(function() {
        this.element.hide().setStyle(this.getEndPosition({x: dimensions.left, y: dimensions.top}));
      })
    } else {
      dimensions = this.element.setStyle('visibility: hidden').show().dimensions();
      var pre_position = {};
      
      if (this.options.direction == 'left') {
        pre_position.x = - dimensions.width - threshold;
        position.x = dimensions.left;
      } else {
        pre_position.y = - dimensions.height - threshold;
        position.y = dimensions.top;
      }
      
      this.element.setStyle(this.getEndPosition(pre_position)).setStyle('visibility: visible');
    }
    
    return this.$super(position);
  }
});
/**
 * The puff visual effect
 *
 * Copyright (C) Nikolay V. Nemshilov aka St.
 */
Fx.Puff = new Class(Fx.Zoom, {
  extend: {
    Options: Object.merge(Fx.Zoom.Options, {
      size: 1.4  // the end/initial size of the element
    })
  },
  
// protected

  prepare: function(how) {
    var how = how || 'toggle', opacity = 0, size = this.options.size;
    
    if (how == 'out' || (how == 'toggle' && this.element.visible())) {
      var initial_style = this.getEndPosition(this._getZoomedStyle(1));
      this.onFinish(function() {
        initial_style.opacity = 1;
        this.element.hide().setStyle(initial_style);
      });
      
    } else {
      this.element.setStyle('visibility: visible').show();
      
      var width = this.element.offsetWidth;
      var initial_style = this.getEndPosition(this._getZoomedStyle(1));
      
      this.onFinish(function() {
        this.element.setStyle(initial_style);
      });
      
      this.element.setStyle(Object.merge(
        this.getEndPosition(this._getZoomedStyle(size)), {
          opacity: 0,
          visibility: 'visible'
        }
      ));
      
      size = width / this.element.offsetWidth;
      opacity = 1;
    }
    
    
    return this.$super(size, {opacity: opacity});
  }
  
});
/**
 * Handles the to-class and from-class visual effects
 *
 * Copyright (C) Nikolay V. Nemshilov aka St.
 */
Fx.CSS = new Class(Fx.Morph, {
  // the list of styles to watch
  STYLES: $w('width height lineHeight opacity borderWidth borderColor padding margin color fontSize backgroundColor marginTop marginLeft marginRight marginBottom top left right bottom'),
  
// protected
  
  prepare: function(add_class, remove_class) {
    // grabbing the end style
    var dummy = this._dummy().addClass(add_class||'').removeClass(remove_class||'');
    var style = this._getStyle(dummy, this.STYLES);
    dummy.remove();
    
    // Opera 10 has some trash in the borderWidth style if it was not set
    if (Browser.Opera && !/^\d+[a-z]+/.test(style.borderWidth))
      delete(style.borderWidth);
    
    // wiring the classes add/remove on-finish
    if (add_class)    this.onFinish(this.element.addClass.bind(this.element, add_class));
    if (remove_class) this.onFinish(this.element.removeClass.bind(this.element, remove_class));
    
    return this.$super(style);
  }
});
/**
 * Element shortcuts for the additional effects
 *
 * @copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */
Element.addMethods({
  /**
   * The move visual effect shortcut
   *
   * @param Object end position x/y or top/left
   * @param Object fx options
   * @return Element self
   */
  move: function(position, options) {
    return this.fx('move', [position, options || {}]); // <- don't replace with arguments
  },
  
  /**
   * The bounce effect shortcut
   *
   * @param Number optional bounce size
   * @param Object fx options
   * @return Element self
   */
  bounce: function() {
    return this.fx('bounce', arguments);
  },
  
  /**
   * The zoom effect shortcut
   *
   * @param mixed the zooming value, see Fx.Zoom#start options
   * @param Object fx options
   * @return Element self
   */
  zoom: function(size, options) {
    return this.fx('zoom', [size, options || {}]);
  },
  
  /**
   * Initiates the Fx.Run effect
   *
   * @param String running direction
   * @param Object fx options
   * @return Element self
   */
  run: function() {
    return this.fx('run', arguments);
  },
  
  /**
   * The puff effect shortcut
   *
   * @param String running direction in|out|toggle
   * @param Object fx options
   * @return Element self
   */
  puff: function() {
    return this.fx('puff', arguments);
  },
  
  /**
   * The Fx.Class effect shortcut
   *
   * @param String css-class name to add
   * @param String css-class name to remove
   * @param Object fx options
   */
  morphToClass: function() {
    var args = $A(arguments);
    if (args[0] === null) args[0] = '';
    
    return this.fx('CSS', args);
  }
});

/**
 * String to JSON export
 *
 * Credits:
 *   Based on the original JSON escaping implementation
 *     http://www.json.org/json2.js
 *
 * @copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */
(function(String_proto) {
  var specials = {'\b': '\\b', '\t': '\\t', '\n': '\\n', '\f': '\\f', '\r': '\\r', '"' : '\\"', '\\': '\\\\'},
  quotables = /[\\\"\x00-\x1f\x7f-\x9f\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g;
  
  // quotes the string
  function quote(string) {
    return string.replace(quotables, function(chr) {
      return specials[chr] || '\\u' + ('0000' + chr.charCodeAt(0).toString(16)).slice(-4);
    });
  };
  
  String_proto.toJSON = function() {
    return '"'+ quote(this) + '"';
  }
  
})(String.prototype);
/**
 * Dates to JSON convertion
 *
 * Credits:
 *   Based on the original JSON escaping implementation
 *     http://www.json.org/json2.js
 *
 * @copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */
(function(Date_proto) {
  var z = function(num) {
    return (num < 10 ? '0' : '')+num;
  };
  
  
  Date_proto.toJSON = function() {
    return this.getUTCFullYear() + '-' +
      z(this.getUTCMonth() + 1)  + '-' +
      z(this.getUTCDate())       + 'T' +
      z(this.getUTCHours())      + ':' +
      z(this.getUTCMinutes())    + ':' +
      z(this.getUTCSeconds())    + 'Z';
  };
  
})(Date.prototype);
/**
 * Number to JSON export
 *
 * @copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */
Number.prototype.toJSON = function() { return String(this+0); };
/**
 * The boolean types to prototype export
 *
 * @copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */
Boolean.prototype.toJSON = function() { return String(this); };
/**
 * Array instances to JSON export
 *
 * @copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */
Array.prototype.toJSON = function() {
  return '['+this.map(JSON.encode).join(',')+']'
};
/**
 * The Hash instances to JSON export
 *
 * Copyright (C) 2009 Nikolay V. Nemshilov
 */
if (window['Hash']) {
  window['Hash'].prototype.toJSON = function() {
    return window['JSON'].encode(this.toObject());
  };
}
/**
 * The generic JSON interface
 *
 * Credits:
 *   Based on the original JSON escaping implementation
 *     http://www.json.org/json2.js
 *
 * @copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */
var JSON = {
  encode: function(value) {
    var result;
    
    if (value === null) {
      result = 'null';
    } else if (value.toJSON) {
      result = value.toJSON();
    } else if (isHash(value)){
      result = [];
      for (var key in value) {
        result.push(key.toJSON()+":"+JSON.encode(value[key]));
      }
      result = '{'+result+'}';
    } else {
      throw "JSON can't encode: "+value;
    }
    
    return result;
  },
  
  // see the original JSON decoder implementation for descriptions http://www.json.org/json2.js
  cx: /[\u0000\u00ad\u0600-\u0604\u070f\u17b4\u17b5\u200c-\u200f\u2028-\u202f\u2060-\u206f\ufeff\ufff0-\uffff]/g,
  
  decode: function(string) {
    if (isString(string) && string) {
      // getting back the UTF-8 symbols
      string = string.replace(JSON.cx, function (a) {
        return '\\u' + ('0000' + a.charCodeAt(0).toString(16)).slice(-4);
      });
      
      // checking the JSON string consistency
      if (/^[\],:{}\s]*$/.test(string.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, '@')
        .replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, ']')
        .replace(/(?:^|:|,)(?:\s*\[)+/g, '')))

          return eval('('+string+')');
    }
    
    throw "JSON parse error: "+string;
  }
};
/**
 * Wraps up the Cooke set/get methods so that the values
 * were automatically exported/imported into JSON strings
 * and it allowed transparent objects and arrays saving
 *
 * @copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */
if (window['Cookie']) {
  (function(Cookie_prototype) {
    var old_set = Cookie_prototype.set,
        old_get = Cookie_prototype.get;
        
    $ext(Cookie_prototype, {
      set: function(value) {
        return old_set.call(this, JSON.encode(value));
      },
      
      get: function() {
        return JSON.decode(old_get.call(this));
      }
    });
  })(Cookie.prototype);
}
/**
 * Better JSON sanitizing for the Xhr requests
 *
 * Copyright (C) 2009 Nikolay V. Nemshilov
 */
Xhr.prototype.sanitizedJSON = function() {
  try {
    return JSON.decode(this.text);
  } catch(e) {
    if (this.secureJSON) {
      throw e;
    } else {
      return null;
    }
  }
};

/**
 * presents the Hash unit
 *
 * Copyright (C) 2008-2009 Nikolay V. Nemshilov aka St. <nemshilov#gma-il>
 */
var Hash = new Class({
  /**
   * constructor
   *
   * @params Object optional initial object (will be cloned)
   */
  initialize: function(object) {
    this.$ = {};
    this.merge(object);
  },
  
  $: null, // keeps the values which intersective with the Hash.prototype
  
  /**
   * checks if the hash has a value associated to the key
   *
   * @param String key
   */
  has: function(key) {
    return (this.prototype[key] ? this.$ : this).hasOwnProperty(key);
  },
  
  /**
   * Sets the value
   *
   * @param String key
   * @param mixed value
   * @return Hash self
   */
  set: function(key, value) {
    (this.prototype[key] ? this.$ : this)[key] = value;
    return this;
  },
  
  /**
   * retrieves a value by the key
   *
   * @param String key
   * @return mixed value or null if not set
   */
  get: function(key) {
    return (this.prototype[key] ? this.$ : this)[key];
  },
  
  /**
   * removes a value associated with the key
   *
   * @param String key
   * .......
   * @return Hash self
   */
  remove: function(callback, scope) {
    var filter =  $A(arguments), callback = isFunction(callback) ? callback : null, scope = scope || this;
    
    return this.each(function(key, value) {
      if (callback ? callback.apply(scope, [key, value, this]) : filter.includes(key))
        delete((this.prototype[key] ? this.$ : this)[key]);
    });
  },
  
  /**
   * extracts the list of the attribute names of the given object
   *
   * @return Array keys list
   */
  keys: function() {
    return this.map(function(key, value) { return key });
  },
  
  /**
   * extracts the list of the attribute values of the hash
   *
   * @return Array values list
   */
  values: function() {
    return this.map(function(key, value) { return value });
  },
  
  /**
   * checks if the object-hash has no keys
   *
   * @return boolean check result
   */
  empty: function() {
    var result = true;
    
    this.each(function() { result = false; $break(); });
    
    return result;
  },
  
  /**
   * iterates the given callback throwgh all the hash key -> value pairs
   *
   * @param Function callback
   * @param Object optional scope
   * @return Hash self
   */
  each: function(callback, scope) {
    try {
      scope = scope || this;
      for (var key in this)
        if (!this.prototype[key])
          callback.apply(scope, [key, this[key], this]);
      
      for (var key in this.$)
        callback.apply(scope, [key, this.$[key], this]);
    } catch(e) { if (!(e instanceof Break)) throw(e); }
    
    return this;
  },
  
  /**
   * returns the list of results of calling the callback
   *
   * @param Function callback
   * @param Object scope
   * @return Array result
   */
  map: function(callback, scope) {
    var result = [], scope = scope || this;
    
    this.each(function(key, value) {
      result.push(callback.apply(scope, [key, value, this]));
    });
    
    return result;
  },
  
  /**
   * creates a copy of the Hash keeping only the key-value pairs
   * which passes check in the callback
   *
   * @param Function callback
   * @param Object optional scope
   * @return Hash new
   */
  filter: function(callback, scope) {
    var result = new Hash, scope = scope || this;
    
    this.each(function(key, value) {
      if (callback.apply(scope, [key, value, this]))
        result.set(key, value);
    });
    
    return result;
  },
  
  /**
   * removes all the items from the hashe where the callback returns true
   *
   * @param Function callback
   * @param Object optional scope
   * @return Hash self
   */
  reject: function(callback, scope) {
    var result = new Hash, scope = scope || this;
    
    this.each(function(key, value) {
      if (!callback.apply(scope, [key, value, this]))
        result.set(key, value);
    });
    
    return result;
  },
  
  /**
   * merges the given objects into the current hash
   *
   * @param Object object
   * ......
   * @return Hash all
   */
  merge: function() {
    var args = arguments;
    for (var i=0; i < args.length; i++) {
      if (isHash(args[i])) {
        if (args[i] instanceof Hash) {
          args[i].each(function(key, value) {
            this.set(key, value);
          }, this);
        } else {
          for (var key in args[i])
            this.set(key, args[i][key]);
        }
      }
    }
    return this;
  },
  
  /**
   * converts the hash into a usual object hash
   *
   * @return Object
   */
  toObject: function() {
    var object = {};
    this.each(function(key, value) { object[key] = value; });
    return object;
  },
  
  /**
   * converts a hash-object into an equivalent url query string
   *
   * @return String query
   */
  toQueryString: function() {
    return Object.toQueryString(this.toObject());
  }
});
/**
 * presents the Range unit
 *
 * Copyright (C) 2008-2009 Nikolay V. Nemshilov aka St. <nemshilov#gma-il>
 */
var NumRange = new Class({
  /**
   * basic constructor
   *
   * @param Number start
   * @param Number end
   */
  initialize: function(start, end, step) {
    this.start = start;
    this.end   = end;
    this.step  = (step || 1).abs() * ( start > end ? 1 : -1);
  },
  
  each: function(callback, scope) {
    var scope = scope || this;
    for (var value=this.start, i=0; value < this.end; value += this.step) {
      callback.call(scope, value, i++, this);
    }
  },
  
  map: function(callback, scope) {
    var result = [], scope = scope || this;
    
    this.each(function(value, i) {
      result.push(callback.call(scope, value, i, this));
    });
    
    return result;
  },
  
  filter: function(callback, scope) {
    var result = [], scope = scope || this;
    
    this.each(function(value, i) {
      if (callback.call(scope, value, i, this)) {
        result.push(value);
      }
    });
    
    return result;
  },
  
  reject: function(callback, scope) {
    var result = [], scope = scope || this;
    
    this.each(function(value, i) {
      if (!callback.call(scope, value, i, this)) {
        result.push(value);
      }
    });
    
    return result;
  }
});
/**
 * The String unit additionals
 *
 * Credits:
 *   The faster trim method is based on the work of Yesudeep Mangalapilly 
 *   http://yesudeep.wordpress.com/2009/07/31/even-faster-string-prototype-trim-implementation-in-javascript/
 *   
 * @copyright (C) 2009 Nikolay V. Nemshilov aka St.
 */

if (String.prototype.trim.toString().include('return')) {
  String.WSPS = [];
  $w("0009 000a 000b 000c 000d 0020 0085 00a0 1680 180e 2000 2001 2002 2003 2004 2005 "+
     "2006 2007 2008 2009 200a 200b 2028 2029 202f 205f 3000").each(function(key) {
       String.WSPS[key.toInt(16)] = 1;
  });
  
  String.prototype.trim = function() {
    var str = this, len = this.length, i = 0;
    if (len) {
      while (String.WSPS[str.charCodeAt(--len)]);
      if (++len) {
        while(String.WSPS[str.charCodeAt(i)]) i++;
      }
      str = str.substring(i, len);
    }
    return str;
  };
}


function $H(object) {
  return new Hash(object);
};

function $R(start, end, step) {
  return new NumRange(start, end, step);
};