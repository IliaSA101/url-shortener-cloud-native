<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

class AuthController extends Controller
{
    /**
     * Авторизация пользователя и выдача API-токена.
     */
    public function store(Request $request)
    {
        // 1. Валидация входящих данных
        $request->validate([
            'email' => 'required|email',
            'password' => 'required',
        ]);

        // 2. Поиск пользователя
        $user = User::where('email', $request->email)->first();

        // 3. Проверка пароля
        if (! $user || ! Hash::check($request->password, $user->password)) {
            // Выбрасываем стандартное исключение валидации, 
            // чтобы фреймворк сам отдал 422 ответ правильного формата.
            throw ValidationException::withMessages([
                'email' => ['Предоставленные учетные данные неверны.'],
            ]);
        }

        // 4. Генерация Sanctum токена
        // 'api-token' — это просто название (полезно, если пользователь авторизуется с разных устройств)
        $token = $user->createToken('api-token')->plainTextToken;

        // 5. Возврат токена
        return response()->json([
            'access_token' => $token,
            'token_type' => 'Bearer',
        ]);
    }
}