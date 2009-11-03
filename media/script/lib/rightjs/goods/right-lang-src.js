/**
 * Additional language level units for RightJS
 *
 * Copyright (C) 2008-2009 Nikolay V. Nemshilov aka St. <nemshilov#gma-il>
 */

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