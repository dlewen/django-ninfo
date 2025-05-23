var app = angular.module('ninfo', ['ngRoute']).
    config(['$routeProvider', function($routeProvider) {
    $routeProvider.
    when('/single',         {templateUrl: '/static/ninfo/partials/single.html', controller: Single}).
    when('/single/:arg*',   {templateUrl: '/static/ninfo/partials/single.html', controller: SingleArg}).
    when('/multiple',       {templateUrl: '/static/ninfo/partials/multiple.html', controller: Multiple}).
    otherwise({redirectTo: '/single'});
    }]);

function Single($scope, $routeParams, $location) {
    $scope.results = []
    $scope.lookup = function(){
        $location.url('/single/' + $scope.arg)
    };
}
function SingleArg($scope, $routeParams, $http, $location) {
    $scope.arg = $routeParams['arg'];
    $scope.lookup = function(){
        $location.url('/single/' + $scope.arg)
    };
    $scope.reset = function () {
        $scope.status = {
            started:false,
            running:0,
            success:0,
            error:0,
            empty:0
        };
    };
    $scope.reset();
    $http.get("/ninfo/api/plugins").success(function(data){
        $scope.plugins = data.plugins;
        $.each(data.plugins, function(i,p){
            p.checked=true;
        });
    });
    $scope.active_plugins = function () {
        var plugins = [];
        angular.forEach($scope.plugins, function(plugin, key){
            if(plugin.checked)
                plugins.push(plugin)
        });
        return plugins;
    };
    $scope.total = function () {
        return $scope.active_plugins().length;
    }

    $scope.bar_success = function() {
        var pct = 100 * ($scope.status.success / $scope.total());
        return {"width": pct + "%"};
    };
    $scope.bar_empty = function() {
        var pct = 100 * ($scope.status.empty / $scope.total());
        return {"width": pct + "%"};
    };
    $scope.bar_error = function() {
        var pct = 100 * ($scope.status.error / $scope.total());
        return {"width": pct + "%"};
    };

    $scope.scroll_to = function(plugin) {
        var selector = "#result_" + plugin;
        var targetOffset = $(selector).offset().top;
        $('html,body').animate({scrollTop: targetOffset-55}, 500);
    };


}
function Multiple($scope, $routeParams, $http) {
    $scope.reset = function () {
        $scope.status = {
            started:false,
            running:0,
            success:0,
            error:0,
            empty:0
        };
        $scope.args=[];
    };
    $scope.reset();
    $http.get("/ninfo/api/plugins").success(function(data){
        $scope.plugins = data.plugins
        $.each(data.plugins, function(i,p){
            p.checked=true;
            $scope.status.total++;
        });
    });
    $scope.lookup = function(){
        $scope.reset();
        var data = {q: $scope.q};
        $http({method:'GET', url: '/ninfo/api/extract', params: data}).success(function(data){
            $scope.args = data.args;
            console.log($scope.args);
            $scope.status.total=0;
            $.each($scope.plugins, function(i, p){
                if(p.checked){
                    $scope.status.total++;
                }
            });
            $scope.status.total *= data.args.length;
        });
    };

    $scope.toggle_all = function () {
        $.each($scope.plugins, function(i, p){
            p.checked = !p.checked;
        });
    };
    $scope.active_plugins = function () {
        var plugins = [];
        angular.forEach($scope.plugins, function(plugin, key){
            if(plugin.checked)
                plugins.push(plugin)
        });
        return plugins;
    };
    $scope.total = function () {
        return $scope.args.length * $scope.active_plugins().length;
    }
    
    $scope.bar_success = function() {
        var pct = 100 * ($scope.status.success / $scope.total());
        return {"width": pct + "%"};
    };
    $scope.bar_empty = function() {
        var pct = 100 * ($scope.status.empty / $scope.total());
        return {"width": pct + "%"};
    };
    $scope.bar_error = function() {
        var pct = 100 * ($scope.status.error / $scope.total());
        return {"width": pct + "%"};
    };
}

app.directive('result', function($http, $sce) {
    return {
        restrict: 'E',
        scope: {arg: '=arg', plugin: '=plugin'},
        link: function($scope, $element, $attrs){
            $scope.result = $sce.trustAsHtml("Loading...");
            $scope.plugin.running = true;
            $scope.plugin.hasResult = false;  // Initialize visibility flag
            $scope.$parent.status.started = true;
            $scope.$parent.status.running++;
            
            $http.get("/ninfo/api/plugins/" + $scope.plugin.name + "/html/" + $scope.arg)
                .success(function(data){
                    if(data && data.trim()) {
                        html = $sce.trustAsHtml(data);
                        $scope.plugin.result = html;
                        $scope.result = html;
                        $scope.plugin.hasResult = true;  // Set visibility flag
                        $scope.$parent.status.success++;
                    } else {
                        $scope.result = null;
                        $scope.plugin.hasResult = false;  // Hide if no content
                        $scope.$parent.status.empty++;
                    }
                    $scope.plugin.running = false;
                    $scope.$parent.status.running--;
                })
                .error(function(){
                    $scope.$parent.status.running--;
                    $scope.$parent.status.error++;
                    $scope.result = null;
                    $scope.plugin.hasResult = false;  // Hide on error
                });
        },
        template:
            '<div class="bg-body-tertiary p-3 rounded mb-3" ng-if="result">' +
            '<h2>{{plugin.title}}</h2>' +
            '<div ng-bind-html="result"></div>' +
            '</div>'
    };
});
