define([
    "dcl/dcl",
    "ind-build/indicator-builder-shim",
    "ind-build/validation"
], function (declare, indicator_builder, validation) {
    "use strict";

    var CERTObservableURI = declare(indicator_builder.ObservableURI, {
        constructor: function () {
            this.type.extend({
                validate: {
                    "isValidCallback": validation.hasValue,
                    "failedValidationMessage": "A URI type is required."
                }
            }).valueHasMutated(); // Have to force a refresh to trigger validation, in batch mode this field isn't visible so the binding isn't re-evaluated.
        },

        doValidation: declare.superCall(function (sup) {
            return function () {
                var msgs = sup.call(this);
                if (this.type.hasError()) {
                    msgs.addError(this.type.errorMessage());
                }
                return msgs;
            };
        })
    });
    indicator_builder.ObservableURI = CERTObservableURI;
    return CERTObservableURI;
});
