function stickyNavbar() {
  const banner = document.getElementById('banner');
  const navbar = document.getElementById('navbar');
  const sticky = banner.offsetTop + banner.offsetHeight;
  if (visualViewport.pageTop >= sticky) {
    if (! navbar.classList.contains('sticky')) {
      const pageTop = visualViewport.pageTop;
      const pageLeft = visualViewport.pageLeft;
      navbar.classList.add('sticky');
      // From what I can tell, adding this class redraws the dom, which changes
      // the offset values in visualViewport. This causes the screen to jump.
      // The following scrollTo corrects this and "jumps back" to where the
      // screen was. I suspect that the offset values will always be 0, but I'd
      // rather be safe.
      // In addition, this acts wonky if the page is short enough that the
      // unexpanded navbar can't reach the top of the page.
      window.scrollTo(pageLeft - visualViewport.offsetLeft,
          pageTop - visualViewport.offsetTop);
    }
  } else {
    navbar.classList.remove('sticky');
  }
}

function navbarOnclick() {
  const navbar = document.getElementById('navbar');
  if (navbar.classList.contains('mobile-navbar-display')) {
    navbar.classList.remove('mobile-navbar-display');
  } else {
    navbar.classList.add('mobile-navbar-display');
  }
}

window.onload = function() {
  window.onscroll = stickyNavbar;
};
