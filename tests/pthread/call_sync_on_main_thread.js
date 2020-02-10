mergeInto(LibraryManager.library, {
  // Test accessing a DOM element on the main thread.
  // This function returns the inner text of the given element
  // Because it accesses the DOM, it must be called on the main thread.
  getDomElementContents__proxy: 'sync',
  getDomElementContents__sig: 'viii',
  getDomElementContents: function(domElementSelector, dst, size) {
    var selector = UTF8ToString(domElementSelector);
    var text = document.querySelector(selector).innerHTML;
    stringToUTF8(text, dst, size);
  },

  receivesAndReturnsAnInteger__proxy: 'sync',
  receivesAndReturnsAnInteger__sig: 'ii',
  receivesAndReturnsAnInteger: function(i) {
    return i + 42;
  },

  isThisInWorker: function() {
    return typeof ENVIRONMENT_IS_WORKER !== 'undefined' && ENVIRONMENT_IS_WORKER;
  },

  isThisInWorkerOnMainThread__proxy: 'sync',
  isThisInWorkerOnMainThread__sig: 'i',
  isThisInWorkerOnMainThread: function() {
    return typeof ENVIRONMENT_IS_WORKER !== 'undefined' && ENVIRONMENT_IS_WORKER;
  }
});
