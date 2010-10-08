
var util = {

  shouldDebug: false,

  // Note: Will fail in pathological cases (where the members contain
  // strings similar to describe() result).
  membersEqual: function(array1, array2) {
    return util.describe(array1)==util.describe(array2);
  },

  describe: function(obj) {
    if (obj==null) { return null; }
    switch(typeof(obj)) {
      case 'object': {
        var message = "";
        for (key in obj) {
          message += ", [" + key + "]: [" + obj[key] + "]";
        }
        if (message.length > 0) {
          message = message.substring(2); // chomp initial ', '
        }
        return message;
      }
      default: return "" + obj;
    }
  },

  debug: function(message) {
      if (this.shouldDebug) {
        alert("AjaxJS Message:\n\n" + message);
      }
  },

  error: function(message) {
      if (this.shouldDebug) {
        alert("AjaxJS ERROR:\n\n" + message);
      }
  },

  trim: function(str) {
    return str.replace(/(^\s+|\s+$)/g,'');
  },

  strip: function(str) {
    return str.replace(/\s+/, "");
  }

}

function $() {

    var elements = new Array();

    for (var i = 0; i < arguments.length; i++) {

      var element = arguments[i];

      if (typeof element == 'string') {
        if (document.getElementById) {
          element = document.getElementById(element);
        } else if (document.all) {
          element = document.all[element];
        }
      }

      elements.push(element);

    }

    if (arguments.length == 1 && elements.length > 0) {
      return elements[0];
    } else {
      return elements;
    }
}

function $C(elType) {
  return document.createElement(elType);
}

// From prototype library. Try.these(f1, f2, f3);
var Try = {
  these: function() {
    var returnValue;
    for (var i = 0; i<arguments.length; i++) {
      var lambda = arguments[i];
      try {
        returnValue = lambda();
        break;
      } catch (e) {}
    }
    return returnValue;
  }
}

function getElementsByClassName(classname) {
    var a = [];
    var re = new RegExp('\\b' + classname + '\\b');
    var els = document.getElementsByTagName("*");
    for(var i=0,j=els.length; i<j; i++)
        if(re.test(els[i].className))a.push(els[i]);
    return a;
}

function extractIFrameBody(iFrameEl) {

  var doc = null;
  if (iFrameEl.contentDocument) { // For NS6
    doc = iFrameEl.contentDocument; 
  } else if (iFrameEl.contentWindow) { // For IE5.5 and IE6
    doc = iFrameEl.contentWindow.document;
  } else if (iFrameEl.document) { // For IE5
    doc = iFrameEl.document;
  } else {
    alert("Error: could not find sumiFrame document");
    return null;
  }
  return doc.body;

}



/* function getElementsByClassName(needle) {



  var xpathResult = document.evaluate('//*[@class = needle]', document, null, 0, null);
  var outArray = new Array();
  while ((outArray[outArray.length] = xpathResult.iterateNext())) {
  }
  return outArray;
}
*/

/*
  function acceptNode(node) {
    if (node.hasAttribute("class")) {
      var c = " " + node.className + " ";
       if (c.indexOf(" " + needle + " ") != -1)
         return NodeFilter.FILTER_ACCEPT;
    }
    return NodeFilter.FILTER_SKIP;
  }

  var treeWalker = document.createTreeWalker(document.documentElement,
                                             NodeFilter.SHOW_ELEMENT,
                                             acceptNode,
                                             true);
  var outArray = new Array();
  if (treeWalker) {
    var node = treeWalker.nextNode();
    while (node) {
      outArray.push(node);
      node = treeWalker.nextNode();
    }
  }
  return outArray;
}

*/
///////////////////////////////////////////////////////////////////////////////
// Used for pattern-specific demos.
///////////////////////////////////////////////////////////////////////////////

var DELAY = 1000;
var steps = 0;
function andThen(action) {
  var delayTime = (++steps * DELAY);
  setTimeout(action, delayTime);
}

function log(message) {
  $("log").innerHTML += message + "<br/>";
}

function createXMLHttpRequest() {
  try { return new ActiveXObject("Msxml2.XMLHTTP");    } catch(e) {}
  try { return new ActiveXObject("Microsoft.XMLHTTP"); } catch(e) {}
  try { return new XMLHttpRequest();                   } catch(e) {}
  alert("XMLHttpRequest not supported");
  return null;
}
