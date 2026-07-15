const getDataLayer = () => {
    if (typeof window === 'undefined') {
        return undefined;
    }
    return window.dataLayer;
};

const readCookie = (name) => {
    if (typeof document === 'undefined' || !document.cookie) {
        return undefined;
    }
    const match = document.cookie.match(new RegExp('(?:^|;\\s*)' + name + '=([^;]+)'));
    if (!match) {
        return undefined;
    }
    return decodeURIComponent(match[1]);
};

const getPlatformType = () => {
    if (typeof window === 'undefined') {
        return 'web';
    }
    const userAgent = window.navigator.userAgent.toLowerCase();
    if (/mobile|iphone|ipad|android/.test(userAgent)) {
        return 'app';
    }
    return 'web';
};

const getPlatformName = () => {
    const tenant = typeof window !== 'undefined' ? window._hitzeTenant : undefined;
    if (tenant === '20min-fr') {
        return '20 minutes';
    }
    if (tenant === 'lematin') {
        return 'Lematin';
    }
    return '20 Minuten';
};

const buildEvent = (overrides) => {
    const event = {
        page_title: 'Hitze Widget',
        page_type: 'channel',
        platform_type: getPlatformType(),
        platform_name: getPlatformName(),
        bid: readCookie('dakt_2_uuid'),
        chart_id: 'chart/heat/livedaten'
    };

    Object.keys(overrides).forEach((key) => {
        event[key] = overrides[key];
    });

    Object.keys(event).forEach((key) => {
        if (event[key] === undefined) {
            delete event[key];
        }
    });

    return event;
};

const push = (eventPayload) => {
    const dataLayer = getDataLayer();
    if (!dataLayer) {
        return;
    }
    dataLayer.push(eventPayload);
};

const trackPageView = () => {
    push(buildEvent({ event: 'page_view' }));
};

const trackSearch = ({ plz, mode, station, distanceKm }) => {
    push(
        buildEvent({
            event: 'interaction',
            event_type: 'interaction',
            interaction_source: 'hitze_widget',
            interaction_name: 'search_plz',
            plz,
            mode,
            station_id: station ? station.id : undefined,
            station_name: station ? station.name : undefined,
            station_canton: station ? station.kt : undefined,
            distance_km: distanceKm,
            result_value: station && typeof station.val === 'number' ? station.val : undefined
        })
    );
};

const trackSearchInvalid = (plzInput) => {
    push(
        buildEvent({
            event: 'interaction',
            event_type: 'interaction',
            interaction_source: 'hitze_widget',
            interaction_name: 'search_plz_invalid',
            plz_input: plzInput,
            reason: 'unknown_plz'
        })
    );
};

const trackModeNow = ({ lastPlz }) => {
    push(
        buildEvent({
            event: 'interaction',
            event_type: 'interaction',
            interaction_source: 'hitze_widget',
            interaction_name: 'mode_now',
            last_plz: lastPlz || undefined
        })
    );
};

const trackModeMax = ({ lastPlz }) => {
    push(
        buildEvent({
            event: 'interaction',
            event_type: 'interaction',
            interaction_source: 'hitze_widget',
            interaction_name: 'mode_max',
            last_plz: lastPlz || undefined
        })
    );
};

window.TrackHitze = {
    trackPageView: trackPageView,
    trackSearch: trackSearch,
    trackSearchInvalid: trackSearchInvalid,
    trackModeNow: trackModeNow,
    trackModeMax: trackModeMax
};
