/** Given the 'arguments' object of a function returns the name of the named function.
 *  This will only work with named functions.
 *  On mozilla browsers, we have the .name property which we can exploit to shorten the code.
 */
 /*
function get_function_name(args){
    var funcName = args.callee['name'] || (function(a){
        var fName = a.callee.toString();
        fName = fName.substr('function '.length);
        fName = fName.substr(0, fName.indexOf('('));
        return fName;
    })(args);
    return funcName;
}
*/

/**
 * Behaves just like the python range() builtin function.
 * Arguments:   [start,] stop[, step]
 * 
 * @start   Number  start value
 * @stop    Number  stop value (excluded from result)
 * @step    Number  skip values by this step size
 *
 * Number.range() -> error: needs more arguments
 * Number.range(4) -> [0, 1, 2, 3]
 * Number.range(0) -> []
 * Number.range(0, 4) -> [0, 1, 2, 3]
 * Number.range(0, 4, 1) -> [0, 1, 2, 3]
 * Number.range(0, 4, -1) -> []
 * Number.range(4, 0, -1) -> [4, 3, 2, 1]
 * Number.range(0, 4, 5) -> [0]
 * Number.range(5, 0, 5) -> []
 *   Number.range(5, 4, 1) -> []
 * Number.range(0, 1, 0) -> error: step cannot be zero
 * Number.range(0.2, 4.0) -> [0, 1, 2, 3]
 */
Number.range = function() {
    var start, end, step;
    var array = [];
    
    switch(arguments.length){
        case 0:
            throw new Error('range() expected at least 1 argument, got 0 - must be specified as [start,] stop[, step]');
            return array;
            // break;
        case 1:
            start = 0;
            end = Math.floor(arguments[0]) - 1;
            step = 1;
            break;
        case 2:
        case 3:
        default:
            start = Math.floor(arguments[0]);
            end = Math.floor(arguments[1]) - 1;
            var s = arguments[2];
            if (typeof s === 'undefined'){
                s = 1;
            } 
            step = Math.floor(s) || (function(){ throw new Error('range() step argument must not be zero'); })();
            break;
    }
    
    if (step > 0){
        for (var i = start; i <= end; i += step){
            array.push(i);
        }    
    } else if (step < 0) {
        step = -step;
        if (start > end){
            for (var i = start; i > end + 1; i -= step){
                array.push(i);
            }
        }
    }
    return array;    
}

