// Site analytics: page views, clicks and document opens, sent to Google Analytics 4 when an ID is configured
// in site.json (ga_id). Every tracked link carries data-track="<event>" plus optional data-* parameters.
(function () {
  var id = (window.SRA && window.SRA.ga) || '';
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  if (id) {
    var s = document.createElement('script');
    s.async = true; s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id);
    document.head.appendChild(s);
    gtag('js', new Date());
    gtag('config', id, {anonymize_ip: true});
  }
  window.track = function (name, params) { if (id) gtag('event', name, params || {}); };
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('[data-track]');
    if (!a) return;
    var p = {};
    for (var k in a.dataset) if (k !== 'track') p[k] = String(a.dataset[k]).slice(0, 100);
    if (a.href) p.link_url = a.href;
    window.track(a.dataset.track, p);
  }, true);
})();
