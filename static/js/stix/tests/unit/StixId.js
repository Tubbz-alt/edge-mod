define([
    "intern!object",
    "intern/chai!assert",
    "stix/StixId"
], function (registerSuite, assert, StixId) {
    "use strict";

    // statics go here

    return registerSuite(function () {

        // suite variables go here

        return {
            name: "stix/StixId",
            "undefined id string": function () {
                assert.throws(
                    function () {
                        new StixId(undefined);
                    },
                    "Identifier must be a string"
                );
            },
            "null id string": function () {
                assert.throws(
                    function () {
                        new StixId(null);
                    },
                    "Identifier must be a string"
                );
            },
            "non-string id string": function () {
                assert.throws(
                    function () {
                        new StixId(NaN);
                    },
                    "Identifier must be a string"
                );
            },
            "invalid id string": function () {
                assert.throws(
                    function () {
                        new StixId("wibble");
                    },
                    "Unable to parse id: wibble"
                );
            },
            "id string contains unknown type": function () {
                assert.throws(
                    function () {
                        new StixId("certuk:wibble-00000000-0000-0000-0000-000000000000");
                    },
                    "Unsupported type: wibble"
                );
            },
            "valid: type matched": function () {
                var actual = new StixId("certuk:coa-00000000-0000-0000-0000-000000000000");
                assert.equal(actual.id(), "certuk:coa-00000000-0000-0000-0000-000000000000");
                assert.equal(actual.type().code, "coa");
                assert.equal(actual.namespace(), "certuk");
            },
            "valid: type alias matched": function () {
                var actual = new StixId("certuk:courseofaction-00000000-0000-0000-0000-000000000000");
                assert.equal(actual.id(), "certuk:courseofaction-00000000-0000-0000-0000-000000000000");
                assert.equal(actual.type().code, "coa");
                assert.equal(actual.namespace(), "certuk");
            }
        }
    });
});
