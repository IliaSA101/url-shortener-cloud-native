<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class RateLimitTest extends TestCase
{
    use RefreshDatabase;

    public function test_link_create_rate_limiter_blocks_excessive_requests(): void
    {
        // Подготовка: создаем юзера и токен
        $user = User::factory()->create();
        $token = $user->createToken('test-token')->plainTextToken;

        $headers = [
            'Authorization' => 'Bearer ' . $token,
        ];

        // У нас лимит 10 запросов в минуту для link-create.
        // Делаем 10 успешных запросов.
        for ($i = 0; $i < 10; $i++) {
            $response = $this->postJson('/api/links', [
                'original_url' => 'https://example.com/page/' . $i,
            ], $headers);

            $response->assertStatus(201); // Запрос прошел
        }

        // 11-й запрос: спамер превышает лимит
        $response = $this->postJson('/api/links', [
            'original_url' => 'https://example.com/spam',
        ], $headers);

        // Проверяем статус 429 Too Many Requests
        $response->assertStatus(429);

        // Проверяем наличие служебных заголовков Rate Limiter'а (важно для фронтенда/клиентов)
        $response->assertHeader('X-RateLimit-Limit'); // Должно быть 10
        $response->assertHeader('X-RateLimit-Remaining', 0); // Не осталось попыток
        $response->assertHeader('Retry-After'); // Фреймворк скажет, сколько секунд ждать
    }

    public function test_auth_token_rate_limiter_blocks_bruteforce(): void
    {
        // У нас лимит 5 попыток в минуту для логина (auth-token).
        for ($i = 0; $i < 5; $i++) {
            $response = $this->postJson('/api/auth/token', [
                'email' => 'hacker@example.com',
                'password' => 'wrong_password',
            ]);
            
            // Мы получаем 422, так как пароль неверный, но главное — мидлварь пропустила запрос
            $response->assertStatus(422);
        }

        // 6-я попытка брутфорса
        $response = $this->postJson('/api/auth/token', [
            'email' => 'hacker@example.com',
            'password' => 'wrong_password',
        ]);

        // Контроллер даже не запустится (Fail Fast), получаем 429
        $response->assertStatus(429);
        $response->assertHeader('Retry-After');
    }
}