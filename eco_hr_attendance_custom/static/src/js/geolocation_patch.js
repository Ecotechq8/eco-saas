/** @odoo-module **/

const originalGetCurrentPosition = navigator.geolocation.getCurrentPosition;

navigator.geolocation.getCurrentPosition = function (successCallback, errorCallback, options) {
    const forcedOptions = Object.assign({}, options, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
    });
    return originalGetCurrentPosition.apply(this, [successCallback, errorCallback, forcedOptions]);
};