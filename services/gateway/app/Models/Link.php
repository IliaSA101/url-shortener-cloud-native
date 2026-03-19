<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class Link extends Model
{
    use HasFactory;

    // Разрешаем массовое заполнение этих полей
    protected $fillable = [
        'short_code',
        'original_url',
        'user_id',
    ];
}