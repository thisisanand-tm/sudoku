'use strict';
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js', {scope:'./', updateViaCache:'none'}).then(registration => registration.update()).catch(error => console.warn('Sudoku offline registration:', error));
  });
}
