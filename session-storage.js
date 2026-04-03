// Begin Button & ContactSalesJoinUs Button are the entry points for AuthPortal SignIn page
const BEGIN_BUTTON_ANCHOR_TAG_ID = "signup-homepage-top-section";
const CONTACT_SALES_JOIN_US_BUTTON_ANCHOR_TAG_ID = "smallMerchantSectionSubmit";

// CompleteYourApplication Button is the entry point for business information page
const COMPLETE_YOUR_APPLICATION_BUTTON_DIV_ID = "complianceAssessmentButton";

const anchorTagElements = [
    document.getElementById(BEGIN_BUTTON_ANCHOR_TAG_ID),
    document.getElementById(CONTACT_SALES_JOIN_US_BUTTON_ANCHOR_TAG_ID),
    document.getElementById(COMPLETE_YOUR_APPLICATION_BUTTON_DIV_ID) ? document.getElementById(COMPLETE_YOUR_APPLICATION_BUTTON_DIV_ID).querySelector('a') : null
    ];
const utmParams = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "keyword", "campaign", "campaignid", "adgroupid", "adid", "gclid", "MarketoID"];

//store campaignParams to session Storage
let queryParams = new URLSearchParams(window.location.search);
utmParams.forEach(utmParam => {
    if (queryParams.has(utmParam)) {
        let utmParamValue = queryParams.get(utmParam).replace(/^"|"$/g, '');
        sessionStorage.setItem(utmParam, decodeURIComponent(utmParamValue));
    }
});

//construct & append campaignParams from sessionStorage
anchorTagElements.forEach(anchorTagElement => {
    if (!anchorTagElement)
        return;

    let utmParamsString = utmParams
        .filter(utmParam => sessionStorage.getItem(utmParam))
        .map(utmParam => `${utmParam}=${sessionStorage.getItem(utmParam)}`)
        .join('&');
    if (utmParamsString)
        anchorTagElement.href += `?${utmParamsString}`;
});
