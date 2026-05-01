/* ==========================================================================
   OCAC — Main JavaScript
   Features: mobile menu, scroll header, back-to-top, fade-in,
             year filter, image lightbox
   ========================================================================== */
(function() {
  'use strict';

  // ---------- Mobile Menu ----------
  var toggle = document.querySelector('.menu-toggle');
  var nav = document.getElementById('site-nav');
  var overlay = document.querySelector('.nav-overlay');

  function closeDrawer() {
    if (!toggle || !nav) return;
    toggle.setAttribute('aria-expanded', 'false');
    nav.classList.remove('is-open');
    if (overlay) overlay.classList.remove('is-active');
    document.body.classList.remove('drawer-open');
  }

  function openDrawer() {
    if (!toggle || !nav) return;
    toggle.setAttribute('aria-expanded', 'true');
    nav.classList.add('is-open');
    if (overlay) overlay.classList.add('is-active');
    document.body.classList.add('drawer-open');
  }

  if (toggle && nav) {
    toggle.addEventListener('click', function() {
      var expanded = this.getAttribute('aria-expanded') === 'true';
      if (expanded) closeDrawer(); else openDrawer();
    });
  }
  if (overlay) overlay.addEventListener('click', closeDrawer);
  // Close on link tap inside drawer
  nav && nav.querySelectorAll('a').forEach(function(a) {
    a.addEventListener('click', function() {
      if (window.matchMedia('(max-width: 640px)').matches) closeDrawer();
    });
  });
  // Close on Escape
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && nav && nav.classList.contains('is-open')) closeDrawer();
  });

  // ---------- Scroll: header shadow ----------
  var header = document.getElementById('site-header');
  var lastScroll = 0;
  if (header) {
    window.addEventListener('scroll', function() {
      if (window.scrollY > 10) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
      lastScroll = window.scrollY;
    }, { passive: true });
  }

  // ---------- Back to Top ----------
  var btn = document.createElement('button');
  btn.className = 'back-to-top';
  btn.innerHTML = '↑';
  btn.setAttribute('aria-label', 'Back to top');
  document.body.appendChild(btn);

  window.addEventListener('scroll', function() {
    btn.classList.toggle('is-visible', window.scrollY > 500);
  }, { passive: true });

  btn.addEventListener('click', function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // ---------- Fade-in Animation ----------
  var observer = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.item-card').forEach(function(card, i) {
    card.style.opacity = '0';
    card.style.transform = 'translateY(16px)';
    card.style.transition = 'opacity 0.5s cubic-bezier(0.25,0.1,0.25,1) ' + (i % 4) * 0.06 + 's, transform 0.5s cubic-bezier(0.25,0.1,0.25,1) ' + (i % 4) * 0.06 + 's';
    observer.observe(card);
  });

  // ---------- Archive Year Switcher ----------
  var switcher = document.getElementById('year-switcher');
  if (switcher) {
    var swYears = switcher.dataset.years.split(',');
    var swTrack = document.getElementById('year-track');
    var swStage = document.getElementById('year-stage');
    var swIdx   = 0;
    var swDots  = [];

    function swShow(idx) {
      var outgoing = swStage.querySelector('.year-section.is-active');
      var incoming = document.getElementById('year-' + swYears[idx]);
      if (!incoming) return;

      if (outgoing && outgoing !== incoming) {
        outgoing.classList.remove('is-active');
        outgoing.classList.add('is-leaving');
        setTimeout(function() { outgoing.classList.remove('is-leaving'); }, 220);
      }

      incoming.classList.add('is-active');
      swIdx = idx;

      swDots.forEach(function(d, i) {
        d.classList.toggle('is-active', i === idx);
      });

      fitCardSmTitles();

      var siteH    = (document.getElementById('site-header') || {}).offsetHeight || 52;
      var archiveH = (document.getElementById('archive-header') || {}).offsetHeight || 40;
      var stageTop = swStage.getBoundingClientRect().top + window.scrollY;
      if (outgoing) {
        window.scrollTo({ top: stageTop - siteH - archiveH - 8, behavior: 'smooth' });
      }
    }

    // Build dot buttons
    swYears.forEach(function(year, i) {
      var dot = document.createElement('button');
      dot.className = 'year-dot';
      dot.textContent = year;
      dot.setAttribute('aria-label', year);
      dot.addEventListener('click', function() { swShow(i); });
      swTrack.appendChild(dot);
      swDots.push(dot);
    });

    // Keyboard left/right navigation
    document.addEventListener('keydown', function(e) {
      if (!document.getElementById('year-switcher')) return;
      if (e.key === 'ArrowLeft' && swIdx > 0) swShow(swIdx - 1);
      if (e.key === 'ArrowRight' && swIdx < swYears.length - 1) swShow(swIdx + 1);
    });

    swShow(0);

    // ---------- Drag the active pill along the dot track ----------
    var isDragging = false;

    // Find which dot index is closest to a given clientX
    function dotIndexAtX(clientX) {
      var closest = swIdx;
      var closestDist = Infinity;
      swDots.forEach(function(dot, i) {
        var rect = dot.getBoundingClientRect();
        var center = rect.left + rect.width / 2;
        var dist = Math.abs(clientX - center);
        if (dist < closestDist) { closestDist = dist; closest = i; }
      });
      return closest;
    }

    // Mouse — start drag only on the active pill
    swTrack.addEventListener('mousedown', function(e) {
      if (!e.target.classList.contains('is-active')) return;
      isDragging = true;
      swTrack.classList.add('is-dragging');
      e.preventDefault();
    });

    document.addEventListener('mousemove', function(e) {
      if (!isDragging) return;
      var idx = dotIndexAtX(e.clientX);
      if (idx !== swIdx) swShow(idx);
    });

    document.addEventListener('mouseup', function() {
      if (!isDragging) return;
      isDragging = false;
      swTrack.classList.remove('is-dragging');
    });

    // Touch — start drag only on the active pill
    swTrack.addEventListener('touchstart', function(e) {
      if (!e.target.classList.contains('is-active')) return;
      isDragging = true;
    }, { passive: true });

    swTrack.addEventListener('touchmove', function(e) {
      if (!isDragging) return;
      var idx = dotIndexAtX(e.touches[0].clientX);
      if (idx !== swIdx) swShow(idx);
    }, { passive: true });

    swTrack.addEventListener('touchend', function() {
      isDragging = false;
    });
  }

  // ---------- Image Lightbox ----------
  function createLightbox() {
    var overlay = document.createElement('div');
    overlay.className = 'lightbox-overlay';
    overlay.innerHTML = '<button class="lightbox-close" aria-label="Close">×</button>' +
      '<button class="lightbox-nav lightbox-prev" aria-label="Previous">‹</button>' +
      '<img src="" alt="">' +
      '<button class="lightbox-nav lightbox-next" aria-label="Next">›</button>';
    document.body.appendChild(overlay);

    var img = overlay.querySelector('img');
    var closeBtn = overlay.querySelector('.lightbox-close');
    var prevBtn = overlay.querySelector('.lightbox-prev');
    var nextBtn = overlay.querySelector('.lightbox-next');
    var images = [];
    var currentIndex = 0;

    function open(src, gallery) {
      images = gallery || [src];
      currentIndex = images.indexOf(src);
      if (currentIndex === -1) currentIndex = 0;
      img.src = images[currentIndex];
      overlay.classList.add('is-active');
      document.body.style.overflow = 'hidden';
      updateNav();
    }

    function close() {
      overlay.classList.remove('is-active');
      document.body.style.overflow = '';
    }

    function navigate(dir) {
      currentIndex = (currentIndex + dir + images.length) % images.length;
      img.src = images[currentIndex];
      updateNav();
    }

    function updateNav() {
      var showNav = images.length > 1;
      prevBtn.style.display = showNav ? '' : 'none';
      nextBtn.style.display = showNav ? '' : 'none';
    }

    closeBtn.addEventListener('click', close);
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) close();
    });
    prevBtn.addEventListener('click', function(e) { e.stopPropagation(); navigate(-1); });
    nextBtn.addEventListener('click', function(e) { e.stopPropagation(); navigate(1); });

    document.addEventListener('keydown', function(e) {
      if (!overlay.classList.contains('is-active')) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowLeft') navigate(-1);
      if (e.key === 'ArrowRight') navigate(1);
    });

    return { open: open };
  }

  var lightbox = createLightbox();

  // Attach to gallery images
  document.querySelectorAll('.article-gallery').forEach(function(gallery) {
    var imgs = gallery.querySelectorAll('img');
    var srcs = Array.prototype.map.call(imgs, function(i) { return i.src; });
    imgs.forEach(function(img) {
      img.addEventListener('click', function() {
        lightbox.open(this.src, srcs);
      });
    });
  });

  // Also attach to article body images (not featured image)
  document.querySelectorAll('.article-body img:not(.article-featured-img)').forEach(function(img) {
    if (img.closest('.article-gallery')) return; // skip gallery images, already handled
    img.style.cursor = 'pointer';
    img.addEventListener('click', function() {
      lightbox.open(this.src);
    });
  });

  // ---------- card-sm: shrink title until info height fits 3:4 image ratio ----------
  function fitCardSmTitles() {
    document.querySelectorAll('.item-card.card-sm').forEach(function(card) {
      var thumb = card.querySelector('.item-thumb');
      var info  = card.querySelector('.item-info');
      var title = card.querySelector('.item-title');
      if (!thumb || !info || !title) return;
      title.style.fontSize = '';
      if (window.matchMedia('(max-width: 640px)').matches) return;
      var maxH  = thumb.offsetWidth * 4 / 3;
      var fs    = parseFloat(getComputedStyle(title).fontSize);
      var minFs = 13;
      while (info.offsetHeight > maxH && fs > minFs) {
        fs -= 1;
        title.style.fontSize = fs + 'px';
      }
    });
  }

  window.addEventListener('load', fitCardSmTitles);
  var fitTimer;
  window.addEventListener('resize', function() {
    clearTimeout(fitTimer);
    fitTimer = setTimeout(fitCardSmTitles, 150);
  });

})();
