define([
    "dcl/dcl",
    "knockout"
], function (declare, ko) {
    "use strict";

    function capitalise(str) {
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }

    function unCamel(str) {
        return str
            .replace(/([a-z])([A-Z])/g, '$1 $2')
            .replace(/\b([A-Z]+)([A-Z])([a-z])/, '$1 $2$3')
            .replace(/^[a-z]/, function (lc) {
                return lc.toUpperCase();
            });
    }

    var valueBuilders = Object.freeze({
        "Boolean": function (rawValue) {
            return rawValue;
        },
        "Number": function (rawValue) {
            return isFinite(rawValue) ? rawValue : null;
        },
        "ObservableString": function (rawValue, deliminator) {
            return rawValue;
        },
        "String": function (rawValue, rawDelimiter) {
            var delimiter = rawDelimiter || "##comma##";
            return rawValue.length > 0 ? rawValue.split(delimiter).join(",") : null;
        },
        "Array": function (rawValue) {
            var builtValue;
            if (rawValue.length > 1) {
                builtValue = typeof rawValue[0] === "object"
                    ? rawValue
                    : rawValue.slice(0, -1).join(", ") + " and " + rawValue[rawValue.length - 1];
            } else if (rawValue.length > 0) {
                builtValue = typeof rawValue[0] === "object" ? rawValue : rawValue[0];
            } else {
                builtValue = null;
            }
            return builtValue;
        },
        "Object": function (rawValue) {
            var condition = rawValue["condition"] || "Equals";
            var applyCondition = rawValue["apply_condition"];
            var builtValue = buildValue(rawValue["value"], rawValue["delimiter"]);
            if (builtValue != null) {
                var parts = [];
                if (applyCondition) {
                    parts.push(capitalise(applyCondition));
                }
                if (condition && condition !== "Equals") {
                    parts.push(unCamel(condition));
                }
                parts.push(builtValue);
                builtValue = parts.join(" ");
            }
            return builtValue;
        }
    });

    function defaultValueBuilder(rawValue) {
        return rawValue ? String(rawValue) : null;
    }

    function buildValue(rawValue, delimiter) {
        if (ko.isObservable(rawValue)) {
            var valueType = "ObservableString";
        } else {
            var valueType = Object.prototype.toString.call(rawValue).slice(8, -1);
        }

        return (valueBuilders[valueType] || defaultValueBuilder)(rawValue, delimiter);
    }

    function isValidState(state) {
        return isFinite(state) && state >= ReviewValue.State.OK && state <= ReviewValue.State.ERROR;
    }

    function getValue(value) {
        var ret = buildValue(value);
        if (ko.isObservable(ret)) {
            return ret();
        }
        return ret;
    };

    //function ReviewValue_hasWarning(rv)
    var ReviewValue = declare(null, {
        declaredClass: "ReviewValue",
        constructor: function (/*Any*/ value, /*State?*/ state, /*String?*/ message) {
            var state = isValidState(state) ? state : ReviewValue.State.OK;

            this.value = getValue(value);

            this.message = (state === ReviewValue.State.OK ? null : message || null);

            this.isEmpty = this.value === null;

            this.hasError = state === ReviewValue.State.ERROR;

            this.hasWarning = state === ReviewValue.State.WARN;

            this.hasInfo = state === ReviewValue.State.INFO;
        }
    });
    ReviewValue.State = Object.freeze({
        parse: function (stateString) {
            var state = ReviewValue.State[stateString];
            if (isValidState(state)) {
                return state;
            } else {
                throw new Error("Invalid state: " + stateString);
            }
        },
        OK: 0,
        INFO: 1,
        WARN: 2,
        ERROR: 3
    });
    return ReviewValue;
});
