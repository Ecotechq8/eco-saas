//function updateSupportLink() {
//    const supportLink = document.querySelector('a[data-menu="support"]');
//    if (supportLink && supportLink.href !== 'https://odoo.ecotech-mena.com/') {
//        supportLink.href = 'https://odoo.ecotech-mena.com/';
//        supportLink.target = '_blank'; // optional: open in new tab
//    }
//}
//
//// Run once on page load
//document.addEventListener('DOMContentLoaded', () => {
//    updateSupportLink();
//
//    // Observe changes to the menu container to fix dynamic reloads
//    const menuContainer = document.querySelector('.o_popover.popover');
//    if (menuContainer) {
//        const observer = new MutationObserver(() => {
//            updateSupportLink();
//        });
//        observer.observe(menuContainer, { childList: true, subtree: true });
//    }
//});