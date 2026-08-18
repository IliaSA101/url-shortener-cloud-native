<?php

namespace App\Providers;

use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        //
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        // 1. Лимитер для общих публичных эндпоинтов
        RateLimiter::for('api-public', function (Request $request) {
            return Limit::perMinute(60)->by($request->ip());
        });

        // 2. Лимитер для авторизованной зоны (по ID пользователя)
        // На случай, если мидлварь повесят на роут без жесткой авторизации, делаем fallback на IP
        RateLimiter::for('api-auth', function (Request $request) {
            return Limit::perMinute(300)->by($request->user('sanctum')?->id ?: $request->ip());
        });

        // 3. Жесткий лимитер для создания ссылок (защита от спама/генерации)
        // Решаем проблему "Fail Fast": проверка авторизации происходит прямо здесь.
        RateLimiter::for('link-create', function (Request $request) {
            $identifier = $request->user('sanctum') ? $request->user('sanctum')->id : $request->ip();
            return Limit::perMinute(10)->by($identifier);
        });

        // 4. Защита от брутфорса паролей (по IP)
        RateLimiter::for('auth-token', function (Request $request) {
            return Limit::perMinute(5)->by($request->ip());
        });
    }
}