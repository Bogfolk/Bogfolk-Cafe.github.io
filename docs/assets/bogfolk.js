function navbarOnclick() {
  const navbar = document.getElementById('navbar');
  if (navbar.classList.contains('mobile-navbar-display')) {
    navbar.classList.remove('mobile-navbar-display');
  } else {
    navbar.classList.add('mobile-navbar-display');
  }
}
