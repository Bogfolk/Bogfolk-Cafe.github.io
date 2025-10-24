function navbarOnclick() {
  const navbar = document.getElementById('navbar');
  if (navbar.classList.contains('mobile-navbar-display')) {
    navbar.classList.remove('mobile-navbar-display');
  } else {
    navbar.classList.add('mobile-navbar-display');
  }
}

function dropdownOnClick(btn) {
  console.log(btn);
  const node = btn.parentNode.parentNode;
  if(node.classList.contains('active')) {
    node.classList.remove('active');
  } else {
    node.classList.add('active');
  }
}
