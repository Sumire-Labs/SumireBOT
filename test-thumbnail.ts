import { ThumbnailBuilder } from 'discord.js';

const thumbnail = new ThumbnailBuilder();
console.log('ThumbnailBuilder methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(thumbnail)));
