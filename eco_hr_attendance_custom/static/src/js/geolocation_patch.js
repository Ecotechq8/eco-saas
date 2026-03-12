/** @odoo-module **/

console.log("DEBUG: Geolocation Patch is initializing...");

const originalGetCurrentPosition = navigator.geolocation.getCurrentPosition;

navigator.geolocation.getCurrentPosition = function (successCallback, errorCallback, options) {
    const forcedOptions = {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0
    };

    console.log("DEBUG: navigator.geolocation.getCurrentPosition called with High Accuracy.");

    const patchedSuccess = function(position) {
        console.log("DEBUG: Geolocation Success!");
        console.log("DEBUG: Latitude: " + position.coords.latitude);
        console.log("DEBUG: Longitude: " + position.coords.longitude);
        console.log("DEBUG: Accuracy (meters): " + position.coords.accuracy);
        successCallback(position);
    };

    const patchedError = function(error) {
        console.error("DEBUG: Geolocation Error Code: " + error.code);
        console.error("DEBUG: Geolocation Error Message: " + error.message);
        errorCallback(error);
    };

    return originalGetCurrentPosition.apply(this, [patchedSuccess, patchedError, forcedOptions]);
};